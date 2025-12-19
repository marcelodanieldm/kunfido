from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


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


class JobOffer(models.Model):
    """
    Modelo para representar ofertas de trabajo/servicios.
    """
    
    STATUS_CHOICES = [
        ('ABIERTA', 'Abierta'),
        ('EN_PROGRESO', 'En Progreso'),
        ('FINALIZADA', 'Finalizada'),
        ('CANCELADA', 'Cancelada'),
    ]
    
    creador = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='ofertas_creadas',
        verbose_name='Creador'
    )
    
    titulo = models.CharField(
        max_length=200,
        verbose_name='Título',
        help_text='Título descriptivo de la oferta'
    )
    
    descripcion = models.TextField(
        verbose_name='Descripción',
        help_text='Descripción detallada del trabajo',
        blank=True
    )
    
    zona = models.CharField(
        max_length=255,
        verbose_name='Zona',
        help_text='Zona geográfica donde se realizará el trabajo'
    )
    
    presupuesto_ars = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Presupuesto (ARS)',
        help_text='Presupuesto estimado en pesos argentinos',
        validators=[MinValueValidator(0)]
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='ABIERTA',
        verbose_name='Estado'
    )
    
    fecha_inicio = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Inicio',
        help_text='Fecha en que se inició el trabajo'
    )
    
    fecha_entrega_pactada = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Entrega Pactada',
        help_text='Fecha comprometida para entregar el trabajo'
    )
    
    fecha_entrega_real = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Entrega Real',
        help_text='Fecha en que se entregó el trabajo'
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
        verbose_name = 'Oferta de Trabajo'
        verbose_name_plural = 'Ofertas de Trabajo'
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"{self.titulo} - {self.zona} (${self.presupuesto_ars})"
    
    @property
    def cantidad_propuestas(self):
        """Retorna la cantidad de propuestas recibidas."""
        return self.propuestas.count()
    
    @property
    def dias_atraso(self):
        """
        Calcula los días de atraso del trabajo.
        Retorna:
        - None: si no hay fecha de entrega pactada o el trabajo no está finalizado
        - 0: si se entregó a tiempo o antes
        - >0: cantidad de días de atraso
        """
        if not self.fecha_entrega_pactada:
            return None
        
        # Si el trabajo está finalizado, usar fecha real
        if self.status == 'FINALIZADA' and self.fecha_entrega_real:
            fecha_comparacion = self.fecha_entrega_real
        else:
            # Si aún no se finalizó, comparar con la fecha actual
            fecha_comparacion = timezone.now()
        
        # Calcular diferencia en días
        diferencia = (fecha_comparacion - self.fecha_entrega_pactada).days
        
        # Retornar 0 si se entregó a tiempo o antes, o los días de atraso
        return max(0, diferencia)


class Proposal(models.Model):
    """
    Modelo para representar propuestas/ofertas de profesionales (OFICIO) 
    a ofertas de trabajo. Permite contraofertas mediante actualización.
    """
    
    oferta = models.ForeignKey(
        JobOffer,
        on_delete=models.CASCADE,
        related_name='propuestas',
        verbose_name='Oferta de Trabajo'
    )
    
    profesional = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='propuestas_enviadas',
        verbose_name='Profesional'
    )
    
    monto = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Monto Propuesto (ARS)',
        help_text='Monto ofrecido por el profesional',
        validators=[MinValueValidator(0)]
    )
    
    dias_entrega = models.PositiveIntegerField(
        verbose_name='Días de Entrega',
        help_text='Cantidad de días estimados para completar el trabajo'
    )
    
    comentario = models.TextField(
        verbose_name='Comentario',
        help_text='Detalles adicionales de la propuesta',
        blank=True
    )
    
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Creación'
    )
    
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name='Última Actualización'
    )
    
    version = models.PositiveIntegerField(
        default=1,
        verbose_name='Versión',
        help_text='Número de versión de la propuesta (contraofertas)'
    )
    
    voto_owner = models.BooleanField(
        default=False,
        verbose_name='Voto del Dueño',
        help_text='Indica si el dueño de la oferta votó esta propuesta'
    )
    
    class Meta:
        verbose_name = 'Propuesta'
        verbose_name_plural = 'Propuestas'
        ordering = ['-fecha_actualizacion']
        unique_together = ['oferta', 'profesional']
    
    def __str__(self):
        return f"{self.profesional.username} -> {self.oferta.titulo} (${self.monto}) v{self.version}"
    
    def save(self, *args, **kwargs):
        """
        Sobrescribe el método save para incrementar la versión
        en actualizaciones (contraofertas).
        """
        if self.pk:  # Si ya existe (es una actualización)
            self.version += 1
        super().save(*args, **kwargs)


class DelayJustification(models.Model):
    """
    Modelo para que los profesionales (OFICIO) justifiquen atrasos en la entrega.
    Permite al cliente aceptar o rechazar la justificación.
    """
    
    oferta = models.ForeignKey(
        JobOffer,
        on_delete=models.CASCADE,
        related_name='justificaciones_atraso',
        verbose_name='Oferta de Trabajo'
    )
    
    profesional = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='justificaciones_enviadas',
        verbose_name='Profesional'
    )
    
    replica = models.TextField(
        verbose_name='Réplica/Justificación',
        help_text='Explicación del profesional sobre el atraso'
    )
    
    dias_atraso_justificados = models.PositiveIntegerField(
        verbose_name='Días de Atraso',
        help_text='Cantidad de días de atraso que se están justificando'
    )
    
    penalizacion_omitida = models.BooleanField(
        default=False,
        verbose_name='Penalización Omitida',
        help_text='Indica si el cliente aceptó la justificación y omitió la penalización'
    )
    
    fecha_aceptacion = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Aceptación',
        help_text='Fecha en que el cliente aceptó la justificación'
    )
    
    aceptada_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='justificaciones_aceptadas',
        verbose_name='Aceptada Por'
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
        verbose_name = 'Justificación de Atraso'
        verbose_name_plural = 'Justificaciones de Atrasos'
        ordering = ['-fecha_creacion']
        unique_together = ['oferta', 'profesional']
    
    def __str__(self):
        estado = "Aceptada" if self.penalizacion_omitida else "Pendiente"
        return f"{self.profesional.username} - {self.oferta.titulo} ({self.dias_atraso_justificados} días) - {estado}"
    
    def aceptar_justificacion(self, aceptado_por):
        """
        Marca la justificación como aceptada y omite la penalización.
        """
        self.penalizacion_omitida = True
        self.fecha_aceptacion = timezone.now()
        self.aceptada_por = aceptado_por
        self.save()
