from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import UserProfile


def home(request):
    """
    Vista principal de la aplicación.
    """
    return render(request, 'usuarios/home.html')


@login_required
def dashboard(request):
    """
    Dashboard principal del usuario con métricas según su rol.
    """
    # Verificar si el usuario tiene perfil
    if not hasattr(request.user, 'profile'):
        UserProfile.objects.create(user=request.user)
    
    # Si no ha seleccionado un rol, redirigir al onboarding
    if not request.user.profile.tipo_rol:
        messages.info(request, 'Por favor, completa tu perfil seleccionando un tipo de rol.')
        return redirect('usuarios:onboarding_rol')
    
    return render(request, 'usuarios/dashboard_home.html')


@login_required
def onboarding_rol(request):
    """
    Vista para seleccionar o cambiar el tipo de rol del usuario.
    """
    # Verificar si el usuario tiene perfil
    if not hasattr(request.user, 'profile'):
        UserProfile.objects.create(user=request.user)
    
    if request.method == 'POST':
        tipo_rol = request.POST.get('tipo_rol')
        zona = request.POST.get('zona', '')
        
        if tipo_rol in ['PERSONA', 'CONSORCIO', 'OFICIO']:
            profile = request.user.profile
            profile.tipo_rol = tipo_rol
            if zona:
                profile.zona = zona
            profile.save()
            
            messages.success(request, f'¡Perfil actualizado! Ahora eres un {profile.get_tipo_rol_display()}.')
            return redirect('usuarios:dashboard')
        else:
            messages.error(request, 'Por favor, selecciona un tipo de rol válido.')
    
    return render(request, 'usuarios/onboarding_rol.html')
