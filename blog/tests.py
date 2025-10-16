from django.test import TestCase
from django.db import IntegrityError
from .models import User,Category,Blog,Comment
from django.utils import timezone
from .serializers import UserSerailizer,CategorySerializer,BlogSerializer,CommentSerializer,RegisterSerializer,PasswordResetSerializer
from .serializers import MyTokenObtainPairSerializer
from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes


# User Model 
#  User creation
#  __str__ method
# Unique email check

# Test User Model
class UserModelTest(TestCase):
    # setup is method in Testcase
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="password123"
        )

    # User creation test
    def test_user_creation(self):
        self.assertEqual(self.user.username, "testuser")
        self.assertFalse(self.user.is_admin)

    # __str__ method test
    def test_user_str_method(self):
        self.assertEqual(str(self.user), "testuser")

    # Unique email test 
    def test_unique_email_try_except(self):
        User.objects.create_user(
            username="user1",
            email="unique@example.com",
            password="password123"
        )

        # Duplicate email 
        try:
            User.objects.create_user(
                username="user2",
                email="unique@example.com",
                password="password123"
            )
            duplicate_created = True
        except IntegrityError:
            duplicate_created = False

        self.assertFalse(duplicate_created)
        

# Category
# :: Creation
# ::__str__ method
# ::Unique name constraint


class CategoryModelTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name="Tech",
            description="Technology related posts"
        )

    def test_category_creation(self):
        self.assertEqual(self.category.name, "Tech")

    def test_category_str_method(self):
        self.assertEqual(str(self.category), "Tech")

    def test_unique_category_name(self):
        with self.assertRaises(IntegrityError):
            Category.objects.create(name="Tech")
            
# Blog
# ::Creation
# ::__str__ method
# :: Auto-publish if publish_at <= now
# :: Author relation
# :: Category relation

#user add a blog 
class BlogModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="blogger",
            email="blogger@example.com",
            password="password123"
        )
        self.category = Category.objects.create(name="Lifestyle")
        self.blog = Blog.objects.create(
            title="My First Blog",
            content="This is some content",
            author=self.user,
            category=self.category,
        )
    def test_blog_creation(self):
        self.assertEqual(self.blog.title, "My First Blog")
        self.assertFalse(self.blog.is_published)
        
    def test_blog_str_method(self):
        self.assertEqual(str(self.blog), "My First Blog")
        
    def test_blog_category_relation(self):
        self.assertEqual(self.blog.category.name, "Lifestyle")

    def test_blog_author_relation(self):
        self.assertEqual(self.blog.author.username, "blogger")
        
    def test_blog_auto_publish(self):
        future_blog = Blog.objects.create(
            title="Future Blog",
            content="Will be published immediately",
            author=self.user,
            category=self.category,
            publish_at=timezone.now()
        )
        self.assertTrue(future_blog.is_published)


# Comment
# ::Creation
# ::__str__ method
# ::soft_delete() method
# ::Author relation
# ::Blog relation


class CommentModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="abc",
            email="abc@.com",
            password="password123"
        )
        
        self.category = Category.objects.create(name="Education")
        self.blog = Blog.objects.create(
            title="Learning Django",
            content="Content about Django",
            author=self.user,
            category=self.category
        )
        self.comment = Comment.objects.create(
            blog=self.blog,
            author=self.user,
            content="This is a comment."
        )
    def test_comment_creation(self):
        self.assertEqual(Comment.objects.count(), 1)
        self.assertEqual(self.comment.content, "This is a comment.")
        
    def test_comment_str_method(self):
        expected_str = f"{self.user.username} on '{self.blog.title}': {self.comment.content[:50]}"
        self.assertEqual(str(self.comment), expected_str)
        
        
    def test_comment_blog_relation(self):
        self.assertEqual(self.comment.blog.title, "Learning Django")

    def test_comment_author_relation(self):
        self.assertEqual(self.comment.author.username, "abc")
        
        

#---------------serializer test
#UserSerializer
# user fields (username, email, is_admin)

class UserSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="password123"
        )
        
    def test_user_serializer_data(self):
        serializer = UserSerailizer(self.user)
        data = serializer.data
        self.assertEqual(data['username'], "testuser")
        self.assertEqual(data['email'], "test@example.com")
        self.assertFalse(data['is_admin'])


#CategorySerializer (name, description)

class CategorySerializerTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name="Tech",
            description="Technology posts"
        )
    def test_category_serializer_data(self):
        serializer = CategorySerializer(self.category)
        data = serializer.data
        self.assertEqual(data['name'], "Tech")
        self.assertEqual(data['description'], "Technology posts")
        
        
# CommentSerializer (content, author, blog)
class CommentSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="commenter", 
            email="commenter@example.com", 
            password="pass")
        self.category = Category.objects.create(name="Science")
        self.blog = Blog.objects.create(
            title="Science Blog", 
            content="Content", 
            author=self.user, 
            category=self.category)
        self.comment = Comment.objects.create(blog=self.blog, author=self.user, content="Nice post!")

    def test_comment_serializer_data(self):
        serializer = CommentSerializer(self.comment)
        data = serializer.data
        self.assertEqual(data['content'], "Nice post!")
        self.assertEqual(data['author']['username'], "commenter")
        self.assertEqual(data['blog'], self.blog.id)
        
        
# BlogSerializer(author and category)
class BlogSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="xyz",
            email="xyz@gmail.com",
            password="password123"
        )
        self.category = Category.objects.create(name="Lifestyle")
        self.blog = Blog.objects.create(
            title="My Blog",
            content="Blog content",
            author=self.user,
            category=self.category
        )
        
    def test_blog_serializer_read_only_fields(self):
        serializer = BlogSerializer(self.blog)
        data = serializer.data
        self.assertEqual(data['title'], "My Blog")
        self.assertEqual(data['author']['username'], "xyz")
        self.assertEqual(data['category']['name'], "Lifestyle")
        
        
        
        
#RegisterSerializer (Valid user creation)    
class RegisterSerializerTest(TestCase):
    def test_register_serializer_valid(self):
        data = {
            "username": "abc",
            "email": "abc@gmail.com",
            "password": "abc@#123",
            "password2": "abc@#123"#password not be be common and must be 8 length 
        }
        serializer = RegisterSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()
        self.assertEqual(user.username, "abc")
        self.assertEqual(user.email, "abc@gmail.com")
        
    def test_register_serializer_password_mismatch(self):
        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "pass123",
            "password2": "pass456"
        }
        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("password", serializer.errors)
        
#PasswordResetSerializer(Valid email,Invalid email)  
class PasswordResetSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="resetuser",
            email="reset@example.com", 
            password="pass")

    def test_valid_email(self):
        serializer = PasswordResetSerializer(data={"email": "reset@example.com"})
        self.assertTrue(serializer.is_valid())

    def test_invalid_email(self):
        serializer = PasswordResetSerializer(data={"email": "invalid@example.com"})
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)
        
        
# MyTokenObtainPairSerializer(Token creation)
class MyTokenObtainPairSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="jwtuser",
            email="jwtuser@example.com",
            password="StrongPass123",
        )
        
        def test_jwt_token(self):
        
          token = MyTokenObtainPairSerializer.get_token(self.user)
          self.assertEqual(token['username'], "jwtuser")
          self.assertEqual(token['email'], "jwtuser@example.com")
          self.assertFalse(token['is_admin'])  
          


