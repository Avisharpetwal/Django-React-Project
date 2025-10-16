# from django.contrib import admin
# from .models import User,Blog,Comment,Category



# admin.site.register(User)
# admin.site.register(Category)
# admin.site.register(Blog)
# admin.site.register(Comment)

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Blog, Comment, Category

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    # Add your custom fields to the admin form
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('is_admin', 'profile_picture')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Info', {'fields': ('is_admin', 'profile_picture')}),
    )

# Register other models normally
admin.site.register(Category)
admin.site.register(Blog)
admin.site.register(Comment)

