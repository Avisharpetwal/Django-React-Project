from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.db import DatabaseError, OperationalError
from django.db.models import Q
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import password_validation
from .models import User, Category, Blog, Comment
from .serializers import (UserSerailizer,CategorySerializer,BlogSerializer,CommentSerializer,RegisterSerializer,
    MyTokenObtainPairSerializer,PasswordResetSerializer,PasswordResetConfirmSerializer)


# REGISTER
@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        try:
            user = serializer.save()
            return Response({"message": "User registered successfully."},status=status.HTTP_201_CREATED)
        except (DatabaseError, OperationalError):
            return Response( {"detail": "Database connection error. Please try again later."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# LOGIN (JWT)
class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        try:
            return super().post(request, *args, **kwargs)
        except (DatabaseError, OperationalError):
            return Response(
                {"detail": "Database connection error. Please try again later."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )


# LOGOUT (Blacklist JWT)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    try:
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"detail": "Refresh token is required."}, status=status.HTTP_400_BAD_REQUEST)

        token = RefreshToken(refresh_token)
        token.blacklist()  # Requires simplejwt blacklist app enabled
        return Response({"message": "User logged out successfully."}, status=status.HTTP_205_RESET_CONTENT)
    except Exception as e:
        return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# CATEGORY VIEWS
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def category_list_create(request):
    if request.method == 'GET':
        categories = Category.objects.all()
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)

    if request.method == 'POST':
        if not request.user.is_admin:
            return Response({"detail": "Only admin can create categories"}, status=status.HTTP_403_FORBIDDEN)
        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# BLOG VIEWS (with filtering/search/mine)
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def blog_list_create(request):
    if request.method == 'GET':
        blogs = Blog.objects.filter(is_published=True)

        # Filter by category
        category_id = request.GET.get('category')
        if category_id:
            blogs = blogs.filter(category_id=category_id)

        # Search by title or content
        search_query = request.GET.get('search')
        if search_query:
            blogs = blogs.filter(Q(title__icontains=search_query) | Q(content__icontains=search_query))

        # Show only user's own blogs
        if request.GET.get('mine') == 'true':
            blogs = blogs.filter(author=request.user)

        serializer = BlogSerializer(blogs, many=True)
        return Response(serializer.data)

    if request.method == 'POST':
        serializer = BlogSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(author=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def blog_detail(request, pk):
    try:
        blog = Blog.objects.get(pk=pk)
    except Blog.DoesNotExist:
        return Response({"detail": "Blog not found"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = BlogSerializer(blog)
        return Response(serializer.data)

    if request.method == 'PUT':
        if blog.author != request.user and not request.user.is_admin:
            return Response({"detail": "Not authorized"}, status=status.HTTP_403_FORBIDDEN)
        serializer = BlogSerializer(blog, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'DELETE':
        if blog.author != request.user and not request.user.is_admin:
            return Response({"detail": "Not authorized"}, status=status.HTTP_403_FORBIDDEN)
        blog.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# COMMENT VIEWS
@api_view(['POST', 'GET'])
@permission_classes([IsAuthenticated])
def comment_list_create(request, blog_id):
    try:
        blog = Blog.objects.get(pk=blog_id)
    except Blog.DoesNotExist:
        return Response({"detail": "Blog not found"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        comments = Comment.objects.filter(blog=blog)
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)

    if request.method == 'POST':
        serializer = CommentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(author=request.user, blog=blog)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# PASSWORD RESET REQUEST
@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_request(request):
    serializer = PasswordResetSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    email = serializer.validated_data['email']

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response(
            {"detail": "If this email exists, a reset link will be sent."},
            status=status.HTTP_200_OK
        )

    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    reset_link = f"http://127.0.0.1:8000/api/auth/reset-password-confirm/{uid}/{token}/"

    send_mail(
        subject="Password Reset",
        message=f"Click the link to reset your password: {reset_link}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
    )

    return Response(
        {"detail": "If this email exists, a reset link will be sent."},
        status=status.HTTP_200_OK
    )


# PASSWORD RESET CONFIRM
@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_confirm(request, uidb64, token):
    serializer = PasswordResetConfirmSerializer(data={**request.data, "uid": uidb64, "token":token})
    serializer.is_valid(raise_exception=True)
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return Response({"detail": "Invalid reset link."}, status=status.HTTP_400_BAD_REQUEST)

    if not default_token_generator.check_token(user, token):
        return Response({"detail": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)

   

    user.set_password(serializer.validated_data['new_password'])
    user.save()

    return Response({"detail": "Password has been reset successfully."}, status=status.HTTP_200_OK)
