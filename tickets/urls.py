from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('tickets/create/', views.create_ticket, name='create_ticket'),
    path('tickets/<uuid:ticket_id>/', views.ticket_detail, name='ticket_detail'),
    path('tickets/check/', views.check_ticket_status, name='check_ticket'),
    path('manage/tickets/', views.manage_tickets, name='manage_tickets'),
    path('manage/my-tickets/', views.my_assigned_tickets, name='my_assigned_tickets'),
]