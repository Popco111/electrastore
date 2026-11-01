from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()

ROLE_MAP = {
    'покупатель': 'buyer',
    'продавец': 'seller',
    'buyer': 'buyer',
    'seller': 'seller',
}

ROLE_LABELS = {
    'buyer': 'Покупатель',
    'seller': 'Продавец',
    'admin': 'Администратор',
}


class UserRegisterSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        validators=[UniqueValidator(
            queryset=User.objects.all(),
            message="Пользователь с таким именем уже существует."
        )]
    )
    password = serializers.CharField(write_only=True)
    # Поле role доступно и на вход, и на выход
    role = serializers.CharField(required=False, default='seller')

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'role')

    def create(self, validated_data):
        raw_role = validated_data.pop('role', 'seller')
        clean_role = ROLE_MAP.get(str(raw_role).strip().lower(), 'seller')

        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password']
        )
        user.role = clean_role
        user.save()
        return user

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Преобразуем 'seller'/'buyer' в понятный текст для фронтенда ('Продавец'/'Покупатель')
        user_role = getattr(instance, 'role', 'seller')
        data['role'] = ROLE_LABELS.get(user_role, user_role)
        return data


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