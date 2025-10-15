from django.urls import path
from .views import (
    register,
    MyTokenObtainPairView,
    logout,
    category_list_create,
    blog_list_create,
    blog_detail,
    comment_list_create,
    password_reset_request,
    password_reset_confirm
)
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    # -------------------------
    # AUTH
    # -------------------------
    path('auth/register/', register, name='register'),
    path('auth/login/', MyTokenObtainPairView.as_view(), name='login'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/logout/', logout, name='logout'),

    # -------------------------
    # CATEGORY
    # -------------------------
    path('categories/', category_list_create, name='category-list-create'),

    # -------------------------
    # BLOG
    # -------------------------
    path('blogs/', blog_list_create, name='blog-list-create'),
    path('blogs/<int:pk>/', blog_detail, name='blog-detail'),

    # -------------------------
    # COMMENTS
    # -------------------------
    path('blogs/<int:blog_id>/comments/', comment_list_create, name='comment-list-create'),

    # -------------------------
    # PASSWORD RESET
    # -------------------------
    path('auth/reset-password/', password_reset_request, name='password-reset-request'),
    path('auth/reset-password-confirm/<str:uidb64>/<str:token>/', password_reset_confirm, name='password-reset-confirm'),
]
