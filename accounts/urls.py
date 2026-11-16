from django.urls import path

from . import views

urlpatterns = [
    path('register/', views.register_api, name='register'),
    path('users/me/password/', views.password_change_api, name='password_change'),
    path('users/me/', views.user_me_api, name='user-me'),
    path('users/', views.user_list_api, name='user-list'),
    path('users/<int:pk>/', views.user_detail_api, name='user-detail'),
    path('users/<int:pk>/role/', views.user_role_api, name='user-role'),
]
