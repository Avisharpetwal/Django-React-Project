from rest_framework import serializers
from .models import User,Category,Blog,Comment
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import password_validation


class UserSerailizer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'is_admin','profile_picture' ,'email']
        read_only_fields = ['is_admin']
        
        
        
        
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description']
   
   
   
   
        
class CommentSerializer(serializers.ModelSerializer):
    author =UserSerailizer(read_only=True)  
    class Meta:
        model = Comment
        fields = ['id', 'blog', 'author', 'content', 'created_at','deleted_at']
        read_only_fields = ['blog','author', 'created_at','deleted_at']



        
class BlogSerializer(serializers.ModelSerializer):
    author = UserSerailizer(read_only=True) 
    category = CategorySerializer(read_only=True)
    category_name = serializers.CharField(write_only=True)
    class Meta:
        model = Blog
        fields = [
            'id','title','content','image','author','category','category_name','created_at','updated_at',
            'is_published','publish_at','deleted_at', ]
        read_only_fields = ['author', 'created_at', 'updated_at', 'deleted_at', 'is_published']
        
        
    def create(self, validated_data):
        category_name = validated_data.pop('category_name')
        # Category ko fetch karo ya create karo
        category, _ = Category.objects.get_or_create(name=category_name)
        # Author set karo
        
        author = validated_data.pop('author', None)
        if not author and self.context.get('request'):
            author = self.context['request'].user
        blog = Blog.objects.create(**validated_data, author=author, category=category)
        return blog
    
    def update(self, instance, validated_data):
        # Agar category_name present ho toh update karo
        category_name = validated_data.pop('category_name', None)
        if category_name:
            category, _ = Category.objects.get_or_create(name=category_name)
            instance.category = category
        
        # Baaki fields update karo
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Save updated instance
        instance.save()
        return instance




class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],

    )
    password2 = serializers.CharField(
        write_only=True,
        required=True,
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2','profile_picture',]

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user
    
    

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        token['email'] = user.email
        token['is_admin'] = user.is_admin
        return token
 
 
    
class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("No account found with this email.")
        return value
    
    

class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Handles resetting the password using UID and token
    """
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[password_validation.validate_password],
    )

    
