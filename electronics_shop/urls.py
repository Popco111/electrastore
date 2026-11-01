from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Добавьте этот импорт:
from store.views import index_page, cart_page

urlpatterns = [
    # Веб-страницы
    path('', index_page, name='home'),
    path('cart/', cart_page, name='cart_page'),

    # Админка и API
    path('admin/', admin.site.urls),
    path('api/users/', include('users.urls')),
    path('api/', include('store.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)