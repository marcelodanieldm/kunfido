from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class UserProfile(models.Model):
    """
    Modelo que extiende el usuario de Django con información adicional.
    """
    
    TIPO_ROL_CHOICES = [
        ('PERSONA', 'Persona'),
        ('CONSORCIO', 'Consorcio'),
        ('OFICIO', 'Oficio'),
    ]
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='Usuario'
    )
    
    tipo_rol = models.CharField(
        max_length=20,
        choices=TIPO_ROL_CHOICES,
        default='PERSONA',
        verbose_name='Tipo de Rol'
    )
    
    zona = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='Zona',
        help_text='Zona geográfica del usuario'
    )
    
    puntuacion = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)],
        verbose_name='Puntuación',
        help_text='Puntuación del usuario (0.0 - 5.0)'
    )
    
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Creación'
    )
    
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name='Última Actualización'
    )
    
    class Meta:
        verbose_name = 'Perfil de Usuario'
        verbose_name_plural = 'Perfiles de Usuarios'
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.get_tipo_rol_display()}"
    
    @property
    def email(self):
        """Retorna el email del usuario."""
        return self.user.email
    
    @property
    def nombre_completo(self):
        """Retorna el nombre completo del usuario."""
        return self.user.get_full_name() or self.user.username
