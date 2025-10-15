from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

# Create your models here.
# User model
class User(AbstractUser):
    is_admin=models.BooleanField(default=False)
    profile_picture=models.ImageField(upload_to="profile_pics/",blank=True, null=True )
    email=models.EmailField(unique=True)
    
    def __str__(self):
        return self.username
    
    
# Category model 
class Category(models.Model):
    name=models.CharField(max_length=100 ,unique=True)
    description=models.TextField(blank=True)
    
    def __str__(self):
        return self.name
    
# Blog model
class Blog(models.Model):
    title=models.CharField(max_length=100)
    content=models.TextField()
    image=models.ImageField(upload_to='blog_image/', blank=True ,null=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blogs')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='blogs')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    is_published = models.BooleanField(default=False)
    publish_at = models.DateTimeField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    
    
    def save(self, *args, **kwargs):
        if self.publish_at and self.publish_at <= timezone.now():
            self.is_published = True
        super().save(*args, **kwargs)
        
    def __str__(self):
        return self.title
  
  
# Comment model  
class Comment(models.Model):
        blog = models.ForeignKey(Blog,on_delete=models.CASCADE, related_name='comments')
        author = models.ForeignKey(User,on_delete=models.CASCADE, related_name='comments')
        content = models.TextField()
        created_at = models.DateTimeField(default=timezone.now)
        deleted_at = models.DateTimeField(null=True, blank=True)
        
        def soft_delete(self):
            self.deleted_at = timezone.now()
            self.save()
    
        def __str__(self):
            return f"{self.author.username} on '{self.blog.title}': {self.content[:50]}"
        

        



    


    
    
    
