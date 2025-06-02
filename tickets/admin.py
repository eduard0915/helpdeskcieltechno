from django.contrib import admin
from django.utils.html import format_html
from .models import Ticket, TicketComment

class TicketCommentInline(admin.TabularInline):
    model = TicketComment
    extra = 0
    readonly_fields = ('created_at',)

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('ticket_id', 'subject', 'requester_name', 'requester_email', 
                    'priority_colored', 'status_colored', 'created_at', 'assigned_to')
    list_filter = ('status', 'priority', 'created_at', 'assigned_to')
    search_fields = ('subject', 'description', 'requester_name', 'requester_email', 'ticket_id')
    readonly_fields = ('ticket_id', 'created_at', 'updated_at', 'closed_at', 'resolution_time')
    fieldsets = (
        ('Ticket Information', {
            'fields': ('ticket_id', 'subject', 'description')
        }),
        ('Requester Information', {
            'fields': ('requester_name', 'requester_email')
        }),
        ('Status and Assignment', {
            'fields': ('status', 'priority', 'assigned_to')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'closed_at', 'resolution_time'),
            'classes': ('collapse',)
        }),
    )
    inlines = [TicketCommentInline]

    def priority_colored(self, obj):
        colors = {
            'urgent': 'red',
            'priority': 'orange',
            'normal': 'blue',
        }
        return format_html(
            '<span style="color: {};">{}</span>',
            colors[obj.priority],
            obj.get_priority_display()
        )
    priority_colored.short_description = 'Priority'

    def status_colored(self, obj):
        colors = {
            'open': 'gray',
            'in_process': 'blue',
            'closed': 'green',
        }
        return format_html(
            '<span style="color: {};">{}</span>',
            colors[obj.status],
            obj.get_status_display()
        )
    status_colored.short_description = 'Status'

@admin.register(TicketComment)
class TicketCommentAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'author_display', 'created_at')
    list_filter = ('created_at', 'author')
    search_fields = ('content', 'author_name', 'ticket__subject')
    readonly_fields = ('created_at',)

    def author_display(self, obj):
        return obj.author.username if obj.author else obj.author_name
    author_display.short_description = 'Author'
