from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal, ROUND_HALF_UP


class JobOffer(models.Model):
    """
    Representa una oferta de trabajo publicada por un cliente (PERSONA o CONSORCIO).
    """
    
    STATUS_CHOICES = [
        ('OPEN', 'Abierta'),
        ('IN_PROGRESS', 'En Progreso'),
        ('CLOSED', 'Cerrada'),
    ]
    
    creator = models.ForeignKey(
        'usuarios.UserProfile',
        on_delete=models.CASCADE,
        related_name='job_offers_created',
        verbose_name='Creador',
        help_text='Perfil del usuario que crea la oferta (debe ser PERSONA o CONSORCIO)'
    )
    
    title = models.CharField(
        max_length=200,
        verbose_name='Título',
        help_text='Título descriptivo del trabajo'
    )
    
    description = models.TextField(
        verbose_name='Descripción',
        help_text='Descripción detallada del trabajo requerido'
    )
    
    budget_base_ars = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Presupuesto Base (ARS)',
        help_text='Presupuesto base en pesos argentinos'
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='OPEN',
        verbose_name='Estado',
        db_index=True
    )
    
    is_consorcio = models.BooleanField(
        default=False,
        verbose_name='Es Consorcio',
        help_text='Indica si la oferta fue creada por un consorcio'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Creación'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Última Actualización'
    )
    
    class Meta:
        verbose_name = 'Oferta de Trabajo'
        verbose_name_plural = 'Ofertas de Trabajo'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['creator', 'status']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"
    
    @property
    def budget_base_usdc(self):
        """
        Convierte el presupuesto base de ARS a USDC usando cotización mockeada.
        1 USDC = 1200 ARS
        """
        EXCHANGE_RATE = Decimal('1200.00')  # 1 USDC = 1200 ARS
        return (self.budget_base_ars / EXCHANGE_RATE).quantize(
            Decimal('0.01'),
            rounding=ROUND_HALF_UP
        )
    
    def get_active_bids(self):
        """Retorna todas las pujas activas para esta oferta."""
        return self.bids.filter(is_active=True).order_by('-created_at')
    
    def get_winning_bid(self):
        """Retorna la puja ganadora si existe."""
        return self.bids.filter(is_winner=True).first()
    
    def can_receive_bids(self):
        """Verifica si la oferta puede recibir nuevas pujas."""
        return self.status == 'OPEN'


class Bid(models.Model):
    """
    Representa una puja (oferta) de un profesional para realizar un trabajo.
    """
    
    job_offer = models.ForeignKey(
        JobOffer,
        on_delete=models.CASCADE,
        related_name='bids',
        verbose_name='Oferta de Trabajo'
    )
    
    professional = models.ForeignKey(
        'usuarios.UserProfile',
        on_delete=models.CASCADE,
        related_name='bids_made',
        verbose_name='Profesional',
        help_text='Perfil del profesional que realiza la puja (debe ser OFICIO)'
    )
    
    amount_ars = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Monto (ARS)',
        help_text='Monto ofrecido en pesos argentinos'
    )
    
    estimated_days = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='Días Estimados',
        help_text='Cantidad de días estimados para completar el trabajo'
    )
    
    pitch_text = models.TextField(
        verbose_name='Propuesta',
        help_text='Texto de presentación y propuesta del profesional'
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name='Activa',
        help_text='Indica si la puja sigue siendo válida'
    )
    
    is_winner = models.BooleanField(
        default=False,
        verbose_name='Ganadora',
        help_text='Indica si esta puja fue seleccionada como ganadora'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Creación'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Última Actualización'
    )
    
    class Meta:
        verbose_name = 'Puja'
        verbose_name_plural = 'Pujas'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['job_offer', '-created_at']),
            models.Index(fields=['professional', '-created_at']),
            models.Index(fields=['is_winner']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['job_offer', 'professional'],
                name='unique_bid_per_professional_per_job',
                condition=models.Q(is_active=True)
            ),
        ]
    
    def __str__(self):
        return f"Puja de {self.professional.user.username} - ${self.amount_ars} ARS"
    
    @property
    def amount_usdc(self):
        """
        Convierte el monto de la puja de ARS a USDC usando cotización mockeada.
        1 USDC = 1200 ARS
        """
        EXCHANGE_RATE = Decimal('1200.00')  # 1 USDC = 1200 ARS
        return (self.amount_ars / EXCHANGE_RATE).quantize(
            Decimal('0.01'),
            rounding=ROUND_HALF_UP
        )
    
    @property
    def total_votes(self):
        """Retorna el total de votos recibidos."""
        return self.votes.count()
    
    def mark_as_winner(self):
        """
        Marca esta puja como ganadora y actualiza el estado de la oferta.
        Solo puede haber una puja ganadora por oferta.
        """
        # Desmarcar cualquier otra puja ganadora en esta oferta
        Bid.objects.filter(job_offer=self.job_offer, is_winner=True).update(is_winner=False)
        
        # Marcar esta puja como ganadora
        self.is_winner = True
        self.save()
        
        # Actualizar el estado de la oferta
        self.job_offer.status = 'IN_PROGRESS'
        self.job_offer.save()
    
    def can_be_voted(self):
        """Verifica si esta puja puede recibir votos."""
        return self.is_active and self.job_offer.status == 'OPEN'


class Vote(models.Model):
    """
    Representa un voto de un usuario hacia una puja específica.
    Sistema de votación para ayudar a seleccionar la mejor oferta.
    """
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='votes_cast',
        verbose_name='Usuario'
    )
    
    bid = models.ForeignKey(
        Bid,
        on_delete=models.CASCADE,
        related_name='votes',
        verbose_name='Puja'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Voto'
    )
    
    class Meta:
        verbose_name = 'Voto'
        verbose_name_plural = 'Votos'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'bid'],
                name='unique_vote_per_user_per_bid'
            ),
        ]
        indexes = [
            models.Index(fields=['bid', '-created_at']),
            models.Index(fields=['user', '-created_at']),
        ]
    
    def __str__(self):
        return f"Voto de {self.user.username} en Puja #{self.bid.id}"
    
    @classmethod
    def toggle_vote(cls, user, bid):
        """
        Alterna el voto de un usuario en una puja.
        Si ya votó, elimina el voto. Si no, crea uno nuevo.
        Retorna (voted: bool, vote: Vote|None)
        """
        try:
            vote = cls.objects.get(user=user, bid=bid)
            vote.delete()
            return (False, None)  # Voto eliminado
        except cls.DoesNotExist:
            vote = cls.objects.create(user=user, bid=bid)
            return (True, vote)  # Voto creado
    
    @classmethod
    def user_has_voted(cls, user, bid):
        """Verifica si un usuario ya votó en una puja específica."""
        return cls.objects.filter(user=user, bid=bid).exists()
    
    @classmethod
    def get_user_votes_for_job(cls, user, job_offer):
        """Retorna todas las pujas de una oferta en las que el usuario ha votado."""
        return cls.objects.filter(
            user=user,
            bid__job_offer=job_offer
        ).select_related('bid')

