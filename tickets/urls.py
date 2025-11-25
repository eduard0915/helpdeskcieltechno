from django.urls import path
from . import views

urlpatterns = [
    path('', views.create_ticket, name='home'),
    path('dashboard/', views.home, name='dashboard'),
    path('tickets/create/', views.create_ticket, name='create_ticket'),
    path('tickets/list/', views.tickets_list, name='tickets_list'),
    path('tickets/<uuid:ticket_id>/', views.ticket_detail, name='ticket_detail'),
    path('tickets/check/', views.check_ticket_status, name='check_ticket'),
    path('tickets/my-tickets/', views.my_tickets, name='my_tickets'),
    path('manage/tickets/', views.manage_tickets, name='manage_tickets'),
    path('manage/my-tickets/', views.my_assigned_tickets, name='my_assigned_tickets'),
]
