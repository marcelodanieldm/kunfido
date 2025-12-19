from django.shortcuts import redirect
from django.urls import reverse
from usuarios.models import UserProfile


class OnboardingMiddleware:
    """
    Middleware que verifica si el usuario necesita completar el onboarding.
    Si el usuario está autenticado pero no ha completado su perfil,
    lo redirige al flujo de onboarding correspondiente.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Solo aplicar para usuarios autenticados
        if request.user.is_authenticated:
            # Excluir rutas de administración, cuentas, assets estáticos
            if not (request.path.startswith('/admin/') or 
                    request.path.startswith('/accounts/') or
                    request.path.startswith('/static/') or
                    request.path.startswith('/media/')):
                
                # URLs exentas del onboarding
                exempt_paths = [
                    '/role-selection/',
                    '/onboarding-form/',
                    '/logout/',
                ]
                
                # Verificar si está en una URL exenta
                is_exempt = any(request.path.startswith(path) for path in exempt_paths)
                
                if not is_exempt:
                    # Crear perfil si no existe
                    profile, created = UserProfile.objects.get_or_create(
                        user=request.user,
                        defaults={'tipo_rol': ''}
                    )
                    
                    # Si el perfil no tiene rol asignado o está vacío, redirigir
                    if not profile.tipo_rol or profile.tipo_rol.strip() == '':
                        return redirect('usuarios:role_selection')
        
        response = self.get_response(request)
        return response
