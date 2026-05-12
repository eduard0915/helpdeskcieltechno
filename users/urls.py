from django.urls import path
from . import views

urlpatterns = [
    # User registration
    path('register/', views.register, name='register'),

    # Staff user management
    path('staff/', views.staff_user_list, name='staff_user_list'),
    path('staff/create/', views.staff_user_create, name='staff_user_create'),
    path('staff/<uuid:pk>/update/', views.staff_user_update, name='staff_user_update'),
    path('staff/<uuid:pk>/delete/', views.staff_user_delete, name='staff_user_delete'),
]
