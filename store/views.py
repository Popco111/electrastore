from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Product, Order, OrderItem, CartItem, Category
from .serializers import (
    ProductSerializer,
    OrderSerializer,
    CategorySerializer,
    CartItemSerializer
)


# 1. Отображение HTML-страниц
def index_page(request):
    return render(request, 'index.html')


def cart_page(request):
    return render(request, 'cart.html')


# 2. Класс прав доступа
class IsSellerOrReadOnly(permissions.BasePermission):
    """
    Разрешает безопасные методы (GET) всем.
    Изменяющие методы (POST, PUT, DELETE) — только продавцам и админам.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(
            request.user and
            request.user.is_authenticated and
            (getattr(request.user, 'role', None) == 'seller' or request.user.is_staff)
        )


# 3. ViewSet для товаров
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsSellerOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(seller=self.request.user)

    def get_queryset(self):
            # Убедитесь, что здесь возвращаются все объекты, а не filter(seller=...)
            return Product.objects.all().order_by('-id')


# 4. ViewSet для категорий
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


# 5. ViewSet для корзины (устраняет ImportError: cannot import name 'CartViewSet')
class CartViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CartItemSerializer

    def get_queryset(self):
        return CartItem.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# 6. ViewSet для заказов
class OrderViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        user = request.user
        cart_items = CartItem.objects.filter(user=user)

        if not cart_items.exists():
            return Response(
                {"detail": "Корзина пуста"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Вычисляем общую сумму
        total_price = sum(
            (item.product.price if item.product else 0) * item.quantity
            for item in cart_items
        )

        # Создаем запись заказа
        order = Order.objects.create(
            user=user,
            total_price=total_price,
            status='pending'
        )

        # Переносим элементы из корзины в позиции заказа и списываем со склада
        for item in cart_items:
            if item.product:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    price=item.product.price,
                    quantity=item.quantity
                )

                if item.product.stock >= item.quantity:
                    item.product.stock -= item.quantity
                    item.product.save()

        # Очищаем корзину пользователя
        cart_items.delete()

        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)