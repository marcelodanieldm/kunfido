from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.db.models import Count, Q
from django.urls import reverse
from django.utils.html import format_html
from .models import UserProfile


class UserProfileInline(admin.StackedInline):
    """
    Inline para mostrar y editar el perfil de usuario dentro del admin de User.
    """
    model = UserProfile
    can_delete = False
    verbose_name = 'Perfil de Usuario'
    verbose_name_plural = 'Perfil de Usuario'
    fields = ('tipo_rol', 'zona', 'puntuacion')


class UserAdmin(BaseUserAdmin):
    """
    Admin personalizado para el modelo User que incluye el perfil.
    """
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_tipo_rol', 'get_zona', 'get_puntuacion', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'profile__tipo_rol')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'profile__zona')
    
    def get_tipo_rol(self, obj):
        """Obtiene el tipo de rol del perfil."""
        if hasattr(obj, 'profile'):
            return obj.profile.get_tipo_rol_display()
        return '-'
    get_tipo_rol.short_description = 'Tipo de Rol'
    
    def get_zona(self, obj):
        """Obtiene la zona del perfil."""
        if hasattr(obj, 'profile'):
            return obj.profile.zona or '-'
        return '-'
    get_zona.short_description = 'Zona'
    
    def get_puntuacion(self, obj):
        """Obtiene la puntuación del perfil."""
        if hasattr(obj, 'profile'):
            return f"{obj.profile.puntuacion:.1f}"
        return '-'
    get_puntuacion.short_description = 'Puntuación'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """
    Admin para el modelo UserProfile.
    """
    list_display = ('user', 'tipo_rol', 'zona', 'puntuacion', 'fecha_creacion')
    list_filter = ('tipo_rol', 'fecha_creacion')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name', 'zona')
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')
    
    fieldsets = (
        ('Información del Usuario', {
            'fields': ('user',)
        }),
        ('Información del Perfil', {
            'fields': ('tipo_rol', 'zona', 'puntuacion')
        }),
        ('Fechas', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )


# Personalizar el índice del admin
class KunfidoAdminSite(admin.AdminSite):
    """
    Admin site personalizado para mostrar estadísticas en el índice.
    """
    site_header = 'Administración de Kunfido'
    site_title = 'Panel de Administración'
    index_title = 'Panel de Control'
    
    def index(self, request, extra_context=None):
        """
        Sobrescribe el método index para agregar estadísticas personalizadas.
        """
        extra_context = extra_context or {}
        
        # Obtener estadísticas de usuarios
        total_usuarios = User.objects.count()
        usuarios_activos = User.objects.filter(is_active=True).count()
        
        # Estadísticas por tipo de rol
        usuarios_por_rol = UserProfile.objects.values('tipo_rol').annotate(
            total=Count('id')
        ).order_by('tipo_rol')
        
        # Crear diccionario de estadísticas
        stats_rol = {
            'PERSONA': 0,
            'CONSORCIO': 0,
            'OFICIO': 0
        }
        
        for item in usuarios_por_rol:
            stats_rol[item['tipo_rol']] = item['total']
        
        # Puntuación promedio por rol
        from django.db.models import Avg
        puntuacion_promedio = UserProfile.objects.aggregate(
            promedio_general=Avg('puntuacion'),
            promedio_persona=Avg('puntuacion', filter=Q(tipo_rol='PERSONA')),
            promedio_consorcio=Avg('puntuacion', filter=Q(tipo_rol='CONSORCIO')),
            promedio_oficio=Avg('puntuacion', filter=Q(tipo_rol='OFICIO'))
        )
        
        # Agregar estadísticas al contexto
        extra_context['estadisticas_usuarios'] = {
            'total_usuarios': total_usuarios,
            'usuarios_activos': usuarios_activos,
            'usuarios_inactivos': total_usuarios - usuarios_activos,
            'por_rol': {
                'persona': stats_rol['PERSONA'],
                'consorcio': stats_rol['CONSORCIO'],
                'oficio': stats_rol['OFICIO'],
            },
            'puntuaciones': {
                'promedio_general': round(puntuacion_promedio['promedio_general'] or 0, 2),
                'promedio_persona': round(puntuacion_promedio['promedio_persona'] or 0, 2),
                'promedio_consorcio': round(puntuacion_promedio['promedio_consorcio'] or 0, 2),
                'promedio_oficio': round(puntuacion_promedio['promedio_oficio'] or 0, 2),
            }
        }
        
        return super().index(request, extra_context=extra_context)


# Crear instancia del admin site personalizado
admin_site = KunfidoAdminSite(name='kunfido_admin')

# Re-registrar el modelo User con el admin personalizado
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

# Registrar modelos en el admin site personalizado
admin_site.register(User, UserAdmin)
admin_site.register(UserProfile, UserProfileAdmin)
