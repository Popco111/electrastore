from django.urls import path
from . import views
from django.urls import path
from . import views

urlpatterns = [
    # Страница каталога (например, /catalog/)
    path('catalog/', views.product_list_view, name='product_list'),

    # Страница детального просмотра товара (например, /product/1/)
    path('product/<int:pk>/', views.product_detail_view, name='product_detail'),

    # Ваши существующие API эндпоинты (для ИИ-поиска, похожих товаров и т.д.)
    path('api/products/<int:pk>/similar/', views.get_similar_products, name='similar_products'),
    path('api/products/search-by-image/', views.search_by_image, name='search_by_image'),
]

urlpatterns = [
    path('products/<int:pk>/similar/', views.get_similar_products, name='similar_products'),
    path('products/search-by-image/', views.search_by_image, name='search_by_image'),
]