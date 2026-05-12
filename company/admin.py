from django.contrib import admin
from .models import Company

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    """Admin configuration for Company model"""
    list_display = ('name', 'email', 'phone', 'created_at', 'updated_at')
    search_fields = ('name', 'email', 'phone')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Company Information', {
            'fields': ('name', 'logo', 'address')
        }),
        ('Contact Information', {
            'fields': ('email', 'phone')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def has_add_permission(self, request):
        # Only allow adding if no company exists yet
        return not Company.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of the company
        return False
