from datetime import date

from django.db.models import Count, F, Sum
from django.db.models.functions import TruncDate
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, status, viewsets
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from orders.models import Order, OrderItem, Payment
from products.models import Product
from products.serializers import ProductWriteSerializer
from users.models import User
from .filters import TransactionFilter
from .serializers import AdminUserSerializer, TransactionSerializer

LOW_STOCK_THRESHOLD = 5


class AdminUserViewSet(mixins.ListModelMixin,
                       mixins.RetrieveModelMixin,
                       mixins.UpdateModelMixin,
                       viewsets.GenericViewSet):
    permission_classes = [IsAdminUser]
    serializer_class = AdminUserSerializer
    queryset = User.objects.prefetch_related('addresses').order_by('id')


class AdminProductViewSet(viewsets.ModelViewSet):
    # Unlike the storefront list, this includes inactive products.
    permission_classes = [IsAdminUser]
    serializer_class = ProductWriteSerializer
    queryset = Product.objects.order_by('id')


class AdminTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAdminUser]
    serializer_class = TransactionSerializer
    queryset = Payment.objects.select_related('order__user').order_by('-created_at')
    filter_backends = [DjangoFilterBackend]
    filterset_class = TransactionFilter


def _parse_date(value, name):
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ValueError(f"{name} must be YYYY-MM-DD") from None


class AdminReportView(APIView):
    """GET ?type=sales|users|inventory&start_date=&end_date= (dates inclusive, optional)."""
    permission_classes = [IsAdminUser]
    REPORT_TYPES = ('sales', 'users', 'inventory')

    def get(self, request):
        report_type = request.query_params.get('type', 'sales')
        if report_type not in self.REPORT_TYPES:
            return Response({'type': [f"Must be one of: {', '.join(self.REPORT_TYPES)}"]},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            start = _parse_date(request.query_params.get('start_date'), 'start_date')
            end = _parse_date(request.query_params.get('end_date'), 'end_date')
        except ValueError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        report = getattr(self, f'_{report_type}_report')(start, end)
        return Response({'type': report_type, 'start_date': start, 'end_date': end, **report})

    @staticmethod
    def _in_range(queryset, field, start, end):
        if start:
            queryset = queryset.filter(**{f'{field}__date__gte': start})
        if end:
            queryset = queryset.filter(**{f'{field}__date__lte': end})
        return queryset

    def _sales_report(self, start, end):
        # Revenue counts only orders that have been paid (or progressed past payment).
        paid = self._in_range(Order.objects.filter(status__in=['PAID', 'SHIPPED', 'DELIVERED']),
                              'created_at', start, end)
        totals = paid.aggregate(orders=Count('id'), items_total=Sum('total_amount'),
                                delivery_total=Sum('delivery_charge'))
        by_day = (paid.annotate(day=TruncDate('created_at')).values('day')
                  .annotate(orders=Count('id'), revenue=Sum(F('total_amount') + F('delivery_charge')))
                  .order_by('day'))
        top_products = (OrderItem.objects.filter(order__in=paid, product__isnull=False)
                        .values('product_id', 'product__name')
                        .annotate(units_sold=Sum('quantity'), revenue=Sum(F('price') * F('quantity')))
                        .order_by('-units_sold')[:10])
        items_total = totals['items_total'] or 0
        delivery_total = totals['delivery_total'] or 0
        return {
            'paid_orders': totals['orders'],
            'items_revenue': items_total,
            'delivery_revenue': delivery_total,
            'total_revenue': items_total + delivery_total,
            'by_day': list(by_day),
            'top_products': list(top_products),
        }

    def _users_report(self, start, end):
        new_users = self._in_range(User.objects.all(), 'date_joined', start, end)
        orders = self._in_range(Order.objects.all(), 'created_at', start, end)
        return {
            'total_users': User.objects.count(),
            'new_users': new_users.count(),
            'active_logins': self._in_range(User.objects.exclude(last_login=None), 'last_login', start, end).count(),
            'users_with_orders': orders.values('user_id').distinct().count(),
            'orders_by_status': {row['status']: row['count']
                                 for row in orders.values('status').annotate(count=Count('id'))},
        }

    def _inventory_report(self, start, end):
        # Inventory is a current snapshot; the date range doesn't apply.
        products = Product.objects.all()
        low_stock = (products.filter(is_active=True, stock__lte=LOW_STOCK_THRESHOLD)
                     .order_by('stock').values('id', 'name', 'stock'))
        return {
            'total_products': products.count(),
            'active_products': products.filter(is_active=True).count(),
            'out_of_stock': products.filter(is_active=True, stock=0).count(),
            'low_stock_threshold': LOW_STOCK_THRESHOLD,
            'low_stock': list(low_stock),
            'stock_value': products.aggregate(value=Sum(F('price') * F('stock')))['value'] or 0,
        }
