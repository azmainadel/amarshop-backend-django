import django_filters
from orders.models import Payment


class TransactionFilter(django_filters.FilterSet):
    # dateRange from the spec, as ?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD (both inclusive).
    start_date = django_filters.DateFilter(field_name='created_at', lookup_expr='date__gte')
    end_date = django_filters.DateFilter(field_name='created_at', lookup_expr='date__lte')
    user = django_filters.NumberFilter(field_name='order__user_id')
    status = django_filters.ChoiceFilter(choices=Payment.PAYMENT_STATUS_CHOICES)

    class Meta:
        model = Payment
        fields = ['start_date', 'end_date', 'user', 'status']
