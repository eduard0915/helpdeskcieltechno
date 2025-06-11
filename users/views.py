from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.urls import reverse

from .forms import UserRegistrationForm, UserProfileForm, StaffUserCreationForm, StaffUserUpdateForm
from .models import UserProfile

def register(request):
    """View for user self-registration"""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        profile_form = UserProfileForm(request.POST)

        if form.is_valid() and profile_form.is_valid():
            user = form.save()
            # Set user as non-staff (client)
            user.is_staff = False
            user.save()

            # Update profile
            user.profile.phone_number = profile_form.cleaned_data.get('phone_number')
            user.profile.company = profile_form.cleaned_data.get('company')
            user.profile.is_client = True
            user.profile.save()

            # Log the user in
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            login(request, user)

            messages.success(request, f'¡Cuenta creada exitosamente! Bienvenido, {user.username}.')
            return redirect('home')
    else:
        form = UserRegistrationForm()
        profile_form = UserProfileForm()

    return render(request, 'users/register.html', {
        'form': form,
        'profile_form': profile_form,
        'title': 'Registro de Usuario'
    })

# Staff user management views
def is_staff_user(user):
    """Check if user is staff"""
    return user.is_staff

@login_required
@user_passes_test(is_staff_user)
def staff_user_list(request):
    """View for listing staff users"""
    users = User.objects.filter(is_staff=True)
    return render(request, 'users/staff_user_list.html', {
        'users': users,
        'title': 'Gestión de Usuarios Staff'
    })

@login_required
@user_passes_test(is_staff_user)
def staff_user_create(request):
    """View for creating staff users"""
    if request.method == 'POST':
        form = StaffUserCreationForm(request.POST)
        profile_form = UserProfileForm(request.POST)

        if form.is_valid() and profile_form.is_valid():
            user = form.save()

            # Update profile
            user.profile.phone_number = profile_form.cleaned_data.get('phone_number')
            user.profile.company = profile_form.cleaned_data.get('company')
            user.profile.save()

            messages.success(request, f'Usuario {user.username} creado exitosamente.')
            return redirect('staff_user_list')
    else:
        form = StaffUserCreationForm()
        profile_form = UserProfileForm()

    return render(request, 'users/staff_user_form.html', {
        'form': form,
        'profile_form': profile_form,
        'title': 'Crear Usuario Staff'
    })

@login_required
@user_passes_test(is_staff_user)
def staff_user_update(request, pk):
    """View for updating staff users"""
    # Get the UserProfile by UUID and then get the associated User
    profile = get_object_or_404(UserProfile, profile_uuid=pk)
    user = profile.user

    if request.method == 'POST':
        form = StaffUserUpdateForm(request.POST, instance=user)
        profile_form = UserProfileForm(request.POST, instance=user.profile)

        if form.is_valid() and profile_form.is_valid():
            form.save()
            profile_form.save()

            messages.success(request, f'Usuario {user.username} actualizado exitosamente.')
            return redirect('staff_user_list')
    else:
        form = StaffUserUpdateForm(instance=user)
        profile_form = UserProfileForm(instance=user.profile)

    return render(request, 'users/staff_user_form.html', {
        'form': form,
        'profile_form': profile_form,
        'user': user,
        'title': 'Actualizar Usuario Staff'
    })

@login_required
@user_passes_test(is_staff_user)
def staff_user_delete(request, pk):
    """View for deleting staff users"""
    # Get the UserProfile by UUID and then get the associated User
    profile = get_object_or_404(UserProfile, profile_uuid=pk)
    user = profile.user

    if request.method == 'POST':
        user.delete()
        messages.success(request, f'Usuario {user.username} eliminado exitosamente.')
        return redirect('staff_user_list')

    return render(request, 'users/staff_user_confirm_delete.html', {
        'user': user,
        'title': 'Eliminar Usuario Staff'
    })
