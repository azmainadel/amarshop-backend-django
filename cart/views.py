from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, mixins, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from .models import Cart, CartItem, SavedItem
from .serializers import CartSerializer, CartItemSerializer, SavedItemSerializer


class CartViewSet(viewsets.GenericViewSet):
    # The cart is a per-user singleton created on demand, so only list + custom actions are exposed.
    permission_classes = [IsAuthenticated]
    serializer_class = CartSerializer

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)

    def get_or_create_cart(self):
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        return cart

    def list(self, request):
        cart = self.get_or_create_cart()
        serializer = self.get_serializer(cart)
        return Response(serializer.data)

    @action(detail=False, methods=["POST"], serializer_class=CartItemSerializer)
    def add_item(self, request):
        cart = self.get_or_create_cart()
        existing = CartItem.objects.filter(cart=cart, product_id=request.data.get('product_id')).first()
        serializer = CartItemSerializer(
            data=request.data,
            context={'existing_quantity': existing.quantity if existing else 0},
        )

        if serializer.is_valid():
            product_id = serializer.validated_data['product_id']
            quantity = serializer.validated_data.get('quantity', 1)

            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                product_id=product_id,
                defaults={'quantity': quantity}
            )

            if not created:
                cart_item.quantity += quantity
                cart_item.save()

            serializer = CartItemSerializer(cart_item)
            return Response(data=serializer.data, status=status.HTTP_201_CREATED)

        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["DELETE"], url_path=r"remove-item/(?P<item_id>\d+)")
    def remove_item(self, request, item_id):
        cart = self.get_or_create_cart()
        cart_item = get_object_or_404(CartItem, cart=cart, id=item_id)
        cart_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["PATCH"], url_path=r"update-item/(?P<item_id>\d+)",
            serializer_class=CartItemSerializer)
    def update_item_quantity(self, request, item_id):
        cart = self.get_or_create_cart()
        cart_item = get_object_or_404(CartItem, cart=cart, id=item_id)

        serializer = CartItemSerializer(
            cart_item,
            data={'quantity': request.data.get('quantity')},
            partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response(data=serializer.data, status=status.HTTP_200_OK)

        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SavedItemViewSet(mixins.ListModelMixin,
                       mixins.CreateModelMixin,
                       mixins.RetrieveModelMixin,
                       mixins.DestroyModelMixin,
                       viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = SavedItemSerializer

    def get_queryset(self):
        return SavedItem.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        # Saving the same product twice is idempotent instead of a unique-constraint 500.
        return self.save_for_later(request)

    @action(detail=False, methods=["POST"], url_path="save-for-later", serializer_class=SavedItemSerializer)
    def save_for_later(self, request):
        serializer = SavedItemSerializer(data=request.data)

        if serializer.is_valid():
            product_id = serializer.validated_data['product_id']
            saved_item, created = SavedItem.objects.get_or_create(product_id=product_id,
                                                                  user=self.request.user)
            return Response(data=SavedItemSerializer(saved_item).data,
                            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["POST"])
    def move_to_cart(self, request, pk=None):
        saved_item = self.get_object()
        cart, created = Cart.objects.get_or_create(user=request.user)

        with transaction.atomic():
            CartItem.objects.get_or_create(
                cart=cart,
                product=saved_item.product,
                defaults={"quantity": 1}
            )
            saved_item.delete()

        return Response(data=CartSerializer(cart).data, status=status.HTTP_201_CREATED)
