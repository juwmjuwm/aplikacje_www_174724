from django.urls import include, path
from rest_framework.routers import SimpleRouter

from . import views

router = SimpleRouter()
router.register(r'users', views.UserViewSet, basename='user')

urlpatterns = [
    path('register/', views.RegisterAPIView.as_view(), name='register'),
    path('users/me/password/', views.UserViewSet.as_view({'post': 'change_password'}), name='password_change'),
    path('', include(router.urls)),
]
