from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from .models import Cart, CartItem, SavedItem
from .serializers import CartSerializer, CartItemSerializer, SavedItemSerializer


class CartViewSet(viewsets.ModelViewSet):
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
        serializer = CartItemSerializer(data=request.data)

        if serializer.is_valid():
            product_id = serializer.validated_data['product_id']
            quantity = serializer.validated_data['quantity']

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

    @action(detail=False, methods=["DELETE"], url_path="remove-item/<item_id>")
    def remove_item(self, request, item_id):
        cart = self.get_or_create_cart()
        cart_item = CartItem.objects.filter(cart=cart, id=item_id)
        cart_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["PATCH"], url_path="update-item/<item_id>")
    def update_item_quantity(self, request, item_id):
        cart = self.get_or_create_cart()
        cart_item = CartItem.objects.filter(cart=cart, id=item_id)

        serializer = CartItemSerializer(
            cart_item,
            data={'quantity': request.data['quantity']},
            partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response(data=serializer.data, status=status.HTTP_200_OK)

        return Response(status=status.HTTP_400_BAD_REQUEST)


class SavedItemViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = SavedItemSerializer

    def get_queryset(self):
        return SavedItem.objects.filter(user=self.request.user)

    @action(detail=False, methods=["POST"], url_path="save-for-later", serializer_class=SavedItemSerializer)
    def save_for_later(self, request):
        serializer = SavedItemSerializer(data=request.data)

        if serializer.is_valid():
            product_id = serializer.validated_data['product_id']
            SavedItem.objects.get_or_create(product_id=product_id,
                                            user=self.request.user)
            return Response(status=status.HTTP_200_OK)

        return Response(status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=["POST"])
    def move_to_cart(self, request):
        cart, created = Cart.objects.get_or_create(user=request.user)
        saved_item = self.get_object()
        
        CartItem.objects.get_or_create(
            cart=cart,
            product=saved_item.product,
            defaults={"quantity": 1}
        )
    
        saved_item.delete()
        return Response(status=status.HTTP_201_CREATED)
