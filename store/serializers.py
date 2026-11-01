from rest_framework import serializers
from .models import Category, Product, CartItem, Order, OrderItem, User
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model

User = get_user_model()

# Словарь для отображения роли пользователю

ROLE_LABELS = {
    'buyer': 'Покупатель',
    'seller': 'Продавец',
    'admin': 'Администратор',
}

# Обратный словарь для валидации входящих данных
REVERSE_ROLE_LABELS = {
    'Покупатель': 'buyer',
    'Продавец': 'seller',
    'buyer': 'buyer',
    'seller': 'seller',
}


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']

class ProductSerializer(serializers.ModelSerializer):
    # Добавляем текстовое имя продавца для корректного отображения на JS-фронтенде
    seller_username = serializers.ReadOnlyField(source='seller.username')
    category_name = serializers.ReadOnlyField(source='category.name')

    class Meta:
        model = Product
        fields = [
            'id', 'title', 'description', 'price', 
            'stock', 'image_url', 'category', 'category_name',
            'seller', 'seller_username', 'created_at'
        ]
        read_only_fields = ['seller']

class CartItemSerializer(serializers.ModelSerializer):
    product_detail = ProductSerializer(source='product', read_only=True)

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_detail', 'quantity']

class OrderItemSerializer(serializers.ModelSerializer):
    product_title = serializers.ReadOnlyField(source='product.title')

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_title', 'quantity', 'price']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'user', 'total_price', 'status', 'created_at', 'items']
        read_only_fields = ['user', 'total_price', 'status']

# serializers.py
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    role = serializers.CharField(write_only=True, required=False, default='seller')

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'role')

    def validate_role(self, value):
        # Преобразуем "Продавец" -> "seller", "Покупатель" -> "buyer"
        return REVERSE_ROLE_LABELS.get(value, 'seller')

    def create(self, validated_data):
        role = validated_data.pop('role', 'seller')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password']
        )
        if hasattr(user, 'role'):
            user.role = role
            user.save()
        return user

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        user_role = getattr(user, 'role', 'seller')
        token['role'] = ROLE_LABELS.get(user_role, user_role)
        token['username'] = user.username
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        user_role = getattr(self.user, 'role', 'seller')
        data['role'] = ROLE_LABELS.get(user_role, user_role)
        data['username'] = self.user.username
        return data