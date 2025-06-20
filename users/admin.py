from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile

# Define an inline admin descriptor for UserProfile model
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'profile'

# Define a new User admin
class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_is_client')

    def get_is_client(self, obj):
        return obj.profile.is_client
    get_is_client.short_description = 'Is Client'
    get_is_client.boolean = True

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
