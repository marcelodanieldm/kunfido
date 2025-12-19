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
    
    is_delayed = models.BooleanField(
        default=False,
        verbose_name='Tiene Atraso',
        help_text='Indica si el trabajo está atrasado respecto a la fecha esperada',
        db_index=True
    )
    
    start_confirmed_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Inicio Confirmada',
        help_text='Fecha en que se confirmó el inicio del trabajo'
    )
    
    expected_completion_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Finalización Esperada',
        help_text='Fecha esperada para completar el trabajo'
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
    
    def check_deadline_status(self):
        """
        Verifica si el trabajo está atrasado comparando la fecha actual 
        con la fecha esperada de finalización.
        
        Actualiza el flag is_delayed si el trabajo está en progreso y 
        ha superado la fecha esperada de finalización.
        
        Returns:
            bool: True si está atrasado, False en caso contrario
        """
        if self.status != 'IN_PROGRESS':
            return False
        
        if not self.expected_completion_date:
            return False
        
        now = timezone.now()
        is_past_deadline = now > self.expected_completion_date
        
        # Actualizar el flag si ha cambiado
        if is_past_deadline != self.is_delayed:
            self.is_delayed = is_past_deadline
            self.save(update_fields=['is_delayed'])
        
        return is_past_deadline
    
    def get_days_delayed(self):
        """
        Calcula la cantidad de días de atraso.
        
        Returns:
            int: Número de días de atraso, 0 si no está atrasado
        """
        if not self.expected_completion_date or self.status != 'IN_PROGRESS':
            return 0
        
        now = timezone.now()
        if now <= self.expected_completion_date:
            return 0
        
        delta = now - self.expected_completion_date
        return delta.days


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
        
        # Actualizar el estado de la oferta y establecer fechas
        job = self.job_offer
        job.status = 'IN_PROGRESS'
        job.start_confirmed_date = timezone.now()
        
        # Calcular fecha esperada de finalización basada en días estimados
        from datetime import timedelta
        job.expected_completion_date = job.start_confirmed_date + timedelta(days=self.estimated_days)
        
        job.save()
    
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


class DelayRegistry(models.Model):
    """
    Registro de atrasos en la entrega de trabajos.
    Implementa el sistema de 'Derecho a Réplica' donde el profesional
    puede justificar el atraso y el cliente puede aceptar o rechazar la explicación.
    """
    
    STATUS_CHOICES = [
        ('PENDING', 'Pendiente de Revisión'),
        ('ACCEPTED', 'Aceptado por Cliente'),
        ('REJECTED', 'Rechazado por Cliente'),
    ]
    
    bid = models.ForeignKey(
        Bid,
        on_delete=models.CASCADE,
        related_name='delay_registries',
        verbose_name='Propuesta',
        help_text='Propuesta/Bid asociada al atraso'
    )
    
    days_delayed = models.PositiveIntegerField(
        verbose_name='Días de Atraso',
        help_text='Cantidad de días de atraso registrados'
    )
    
    reason = models.TextField(
        verbose_name='Justificación del Atraso',
        help_text='Explicación del profesional sobre las razones del atraso'
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING',
        verbose_name='Estado',
        help_text='Estado de la justificación'
    )
    
    accepted_by_client = models.BooleanField(
        default=False,
        verbose_name='Aceptado por Cliente',
        help_text='Indica si el cliente aceptó la justificación del atraso'
    )
    
    penalty_applied = models.BooleanField(
        default=False,
        verbose_name='Penalización Aplicada',
        help_text='Indica si se aplicó penalización al profesional'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Creación'
    )
    
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Revisión',
        help_text='Fecha en que el cliente revisó la justificación'
    )
    
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='delay_reviews',
        verbose_name='Revisado Por',
        help_text='Usuario que revisó la justificación'
    )
    
    class Meta:
        verbose_name = 'Registro de Atraso'
        verbose_name_plural = 'Registros de Atrasos'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['bid', '-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['accepted_by_client']),
        ]
    
    def __str__(self):
        return f"Atraso de {self.days_delayed} días - {self.bid.professional.nombre_completo}"
    
    def accept_delay(self, reviewed_by_user):
        """
        El cliente acepta la justificación del atraso.
        Esto resetea/previene la penalización de puntaje.
        
        Args:
            reviewed_by_user: Usuario que acepta el atraso
        """
        self.status = 'ACCEPTED'
        self.accepted_by_client = True
        self.reviewed_at = timezone.now()
        self.reviewed_by = reviewed_by_user
        self.penalty_applied = False
        self.save()
        
        # Si había una penalización aplicada, revertirla
        if self.penalty_applied:
            # Aquí puedes implementar lógica para revertir penalizaciones
            # Por ejemplo, restaurar puntos al profesional
            pass
    
    def reject_delay(self, reviewed_by_user):
        """
        El cliente rechaza la justificación del atraso.
        Se aplica la penalización correspondiente.
        
        Args:
            reviewed_by_user: Usuario que rechaza el atraso
        """
        self.status = 'REJECTED'
        self.accepted_by_client = False
        self.reviewed_at = timezone.now()
        self.reviewed_by = reviewed_by_user
        self.save()
        
        # Aplicar penalización si no se ha aplicado ya
        if not self.penalty_applied:
            self.apply_penalty()
    
    def apply_penalty(self):
        """
        Aplica penalización al profesional por el atraso.
        Reduce el puntaje basado en los días de atraso.
        """
        if self.penalty_applied:
            return
        
        professional = self.bid.professional
        professional.aplicar_penalizacion(self.days_delayed)
        
        self.penalty_applied = True
        self.save(update_fields=['penalty_applied'])
    
    @classmethod
    def create_delay_report(cls, bid, reason):
        """
        Crea un nuevo reporte de atraso para una propuesta.
        
        Args:
            bid: La propuesta (Bid) con atraso
            reason: Justificación del profesional
        
        Returns:
            DelayRegistry: El registro creado
        """
        job = bid.job_offer
        days_delayed = job.get_days_delayed()
        
        return cls.objects.create(
            bid=bid,
            days_delayed=days_delayed,
            reason=reason
        )
    
    @classmethod
    def get_pending_for_job(cls, job_offer):
        """
        Obtiene todos los registros de atraso pendientes para una oferta.
        
        Args:
            job_offer: La oferta de trabajo
        
        Returns:
            QuerySet: Registros de atraso pendientes
        """
        return cls.objects.filter(
            bid__job_offer=job_offer,
            status='PENDING'
        ).select_related('bid__professional__user')


class EscrowTransaction(models.Model):
    """
    Representa una transacción de garantía (escrow) para proteger pagos.
    
    El sistema funciona así:
    1. Al aceptar una propuesta, el 30% se bloquea en escrow (LOCKED)
    2. Cuando el cliente confirma 'Inicio de Obra', se libera el 30% al profesional (RELEASED)
    3. El 70% restante se bloquea cuando se confirma el inicio
    4. Al finalizar la obra, se libera el 70% menos la comisión del 5% (RELEASED)
    5. Si hay problemas, se puede reembolsar al cliente (REFUNDED)
    """
    
    STATUS_CHOICES = [
        ('LOCKED', 'Bloqueado en Escrow'),
        ('RELEASED', 'Liberado al Profesional'),
        ('REFUNDED', 'Reembolsado al Cliente'),
    ]
    
    TRANSACTION_TYPE_CHOICES = [
        ('INITIAL_DEPOSIT', 'Depósito Inicial (30%)'),
        ('REMAINING_DEPOSIT', 'Depósito Restante (70%)'),
        ('INITIAL_RELEASE', 'Liberación Inicial (30%)'),
        ('FINAL_RELEASE', 'Liberación Final (70% - 5%)'),
        ('PLATFORM_FEE', 'Comisión Plataforma (5%)'),
        ('REFUND', 'Reembolso'),
    ]
    
    job = models.ForeignKey(
        JobOffer,
        on_delete=models.CASCADE,
        related_name='escrow_transactions',
        verbose_name='Oferta de Trabajo'
    )
    
    bid = models.ForeignKey(
        Bid,
        on_delete=models.CASCADE,
        related_name='escrow_transactions',
        verbose_name='Propuesta Aceptada'
    )
    
    amount_usdc = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Monto (USDC)',
        help_text='Monto en USDC de la transacción'
    )
    
    transaction_type = models.CharField(
        max_length=30,
        choices=TRANSACTION_TYPE_CHOICES,
        verbose_name='Tipo de Transacción'
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='LOCKED',
        verbose_name='Estado'
    )
    
    from_wallet = models.ForeignKey(
        'usuarios.Wallet',
        on_delete=models.PROTECT,
        related_name='escrow_debits',
        verbose_name='Wallet Origen',
        null=True,
        blank=True
    )
    
    to_wallet = models.ForeignKey(
        'usuarios.Wallet',
        on_delete=models.PROTECT,
        related_name='escrow_credits',
        verbose_name='Wallet Destino',
        null=True,
        blank=True
    )
    
    description = models.TextField(
        blank=True,
        verbose_name='Descripción',
        help_text='Detalles de la transacción'
    )
    
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Metadata',
        help_text='Información adicional en formato JSON'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Creación'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Última Actualización'
    )
    
    released_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Liberación',
        help_text='Fecha en que se liberó el pago'
    )
    
    class Meta:
        verbose_name = 'Transacción de Escrow'
        verbose_name_plural = 'Transacciones de Escrow'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['job', '-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['transaction_type']),
        ]
    
    def __str__(self):
        return f"{self.get_transaction_type_display()} - ${self.amount_usdc} USDC - {self.get_status_display()}"
    
    @classmethod
    def lock_initial_deposit(cls, job, bid, client_wallet):
        """
        Bloquea el 30% (seña) del monto total cuando se acepta una propuesta.
        
        Args:
            job: JobOffer aceptada
            bid: Bid ganadora
            client_wallet: Wallet del cliente
        
        Returns:
            (EscrowTransaction, success: bool, error_msg: str)
        """
        total_amount = bid.amount_usdc
        initial_deposit = (total_amount * Decimal('0.30')).quantize(
            Decimal('0.01'),
            rounding=ROUND_HALF_UP
        )
        
        # Verificar saldo suficiente
        if not client_wallet.tiene_saldo_suficiente(initial_deposit):
            return None, False, "Saldo insuficiente. Por favor, cargue fondos en su wallet."
        
        # Obtener wallet de escrow de la plataforma
        from usuarios.models import Wallet
        escrow_wallet = Wallet.get_escrow_account()
        
        try:
            # Transferir fondos del cliente al escrow
            client_wallet.restar_saldo(initial_deposit)
            escrow_wallet.sumar_saldo(initial_deposit)
            
            # Crear registro de transacción
            transaction = cls.objects.create(
                job=job,
                bid=bid,
                amount_usdc=initial_deposit,
                transaction_type='INITIAL_DEPOSIT',
                status='LOCKED',
                from_wallet=client_wallet,
                to_wallet=escrow_wallet,
                description=f"Depósito inicial del 30% (${initial_deposit} USDC) bloqueado en escrow para '{job.title}'",
                metadata={
                    'total_amount': str(total_amount),
                    'percentage': '30',
                    'professional_id': bid.professional.id,
                    'client_id': client_wallet.user.id
                }
            )
            
            return transaction, True, ""
            
        except Exception as e:
            return None, False, f"Error al procesar transacción: {str(e)}"
    
    @classmethod
    def release_initial_payment(cls, job, bid):
        """
        Libera el 30% inicial al profesional cuando el cliente confirma 'Inicio de Obra'.
        
        Args:
            job: JobOffer en progreso
            bid: Bid ganadora
        
        Returns:
            (EscrowTransaction, success: bool, error_msg: str)
        """
        # Buscar el depósito inicial bloqueado
        initial_deposit = cls.objects.filter(
            job=job,
            bid=bid,
            transaction_type='INITIAL_DEPOSIT',
            status='LOCKED'
        ).first()
        
        if not initial_deposit:
            return None, False, "No se encontró depósito inicial bloqueado."
        
        # Obtener wallets
        from usuarios.models import Wallet
        escrow_wallet = Wallet.get_escrow_account()
        professional_wallet, _ = Wallet.objects.get_or_create(
            user=bid.professional.user,
            defaults={'tipo_cuenta': 'USER', 'balance_usdc': Decimal('0.00')}
        )
        
        try:
            # Transferir del escrow al profesional
            amount = initial_deposit.amount_usdc
            escrow_wallet.restar_saldo(amount)
            professional_wallet.sumar_saldo(amount)
            
            # Actualizar transacción original
            initial_deposit.status = 'RELEASED'
            initial_deposit.released_at = timezone.now()
            initial_deposit.to_wallet = professional_wallet
            initial_deposit.save()
            
            # Crear registro de liberación
            release_transaction = cls.objects.create(
                job=job,
                bid=bid,
                amount_usdc=amount,
                transaction_type='INITIAL_RELEASE',
                status='RELEASED',
                from_wallet=escrow_wallet,
                to_wallet=professional_wallet,
                description=f"Liberación del 30% inicial (${amount} USDC) a {bid.professional.nombre_completo} por '{job.title}'",
                released_at=timezone.now(),
                metadata={
                    'original_deposit_id': initial_deposit.id,
                    'percentage': '30'
                }
            )
            
            return release_transaction, True, ""
            
        except Exception as e:
            return None, False, f"Error al liberar pago: {str(e)}"
    
    @classmethod
    def lock_remaining_amount(cls, job, bid, client_wallet):
        """
        Bloquea el 70% restante cuando se confirma el inicio de obra.
        
        Args:
            job: JobOffer en progreso
            bid: Bid ganadora
            client_wallet: Wallet del cliente
        
        Returns:
            (EscrowTransaction, success: bool, error_msg: str)
        """
        total_amount = bid.amount_usdc
        remaining_amount = (total_amount * Decimal('0.70')).quantize(
            Decimal('0.01'),
            rounding=ROUND_HALF_UP
        )
        
        # Verificar saldo suficiente
        if not client_wallet.tiene_saldo_suficiente(remaining_amount):
            return None, False, "Saldo insuficiente para bloquear el 70% restante."
        
        from usuarios.models import Wallet
        escrow_wallet = Wallet.get_escrow_account()
        
        try:
            # Transferir fondos del cliente al escrow
            client_wallet.restar_saldo(remaining_amount)
            escrow_wallet.sumar_saldo(remaining_amount)
            
            # Crear registro de transacción
            transaction = cls.objects.create(
                job=job,
                bid=bid,
                amount_usdc=remaining_amount,
                transaction_type='REMAINING_DEPOSIT',
                status='LOCKED',
                from_wallet=client_wallet,
                to_wallet=escrow_wallet,
                description=f"Depósito del 70% restante (${remaining_amount} USDC) bloqueado en escrow para '{job.title}'",
                metadata={
                    'total_amount': str(total_amount),
                    'percentage': '70',
                    'professional_id': bid.professional.id
                }
            )
            
            return transaction, True, ""
            
        except Exception as e:
            return None, False, f"Error al bloquear monto restante: {str(e)}"
    
    @classmethod
    def release_final_payment(cls, job, bid):
        """
        Libera el 70% restante menos la comisión del 5% al finalizar la obra.
        
        Args:
            job: JobOffer finalizada
            bid: Bid ganadora
        
        Returns:
            (release_transaction, fee_transaction, success: bool, error_msg: str)
        """
        # Buscar el depósito restante bloqueado
        remaining_deposit = cls.objects.filter(
            job=job,
            bid=bid,
            transaction_type='REMAINING_DEPOSIT',
            status='LOCKED'
        ).first()
        
        if not remaining_deposit:
            return None, None, False, "No se encontró depósito restante bloqueado."
        
        # Calcular comisión del 5% sobre el monto total
        total_amount = bid.amount_usdc
        platform_fee = (total_amount * Decimal('0.05')).quantize(
            Decimal('0.01'),
            rounding=ROUND_HALF_UP
        )
        
        # Monto neto que recibe el profesional = 70% - 5% del total
        amount_to_professional = remaining_deposit.amount_usdc - platform_fee
        
        # Obtener wallets
        from usuarios.models import Wallet
        escrow_wallet = Wallet.get_escrow_account()
        professional_wallet, _ = Wallet.objects.get_or_create(
            user=bid.professional.user,
            defaults={'tipo_cuenta': 'USER', 'balance_usdc': Decimal('0.00')}
        )
        
        try:
            # Transferir del escrow al profesional (70% - 5%)
            escrow_wallet.restar_saldo(remaining_deposit.amount_usdc)
            professional_wallet.sumar_saldo(amount_to_professional)
            # La comisión (5%) queda en el escrow como ganancia de la plataforma
            escrow_wallet.sumar_saldo(platform_fee)
            
            # Actualizar transacción original
            remaining_deposit.status = 'RELEASED'
            remaining_deposit.released_at = timezone.now()
            remaining_deposit.to_wallet = professional_wallet
            remaining_deposit.save()
            
            # Crear registro de liberación final
            release_transaction = cls.objects.create(
                job=job,
                bid=bid,
                amount_usdc=amount_to_professional,
                transaction_type='FINAL_RELEASE',
                status='RELEASED',
                from_wallet=escrow_wallet,
                to_wallet=professional_wallet,
                description=f"Liberación final del 70% (${amount_to_professional} USDC) a {bid.professional.nombre_completo} por '{job.title}'",
                released_at=timezone.now(),
                metadata={
                    'original_deposit_id': remaining_deposit.id,
                    'percentage': '65',  # 70% - 5% = 65%
                    'fee_deducted': str(platform_fee)
                }
            )
            
            # Crear registro de comisión
            fee_transaction = cls.objects.create(
                job=job,
                bid=bid,
                amount_usdc=platform_fee,
                transaction_type='PLATFORM_FEE',
                status='RELEASED',
                from_wallet=escrow_wallet,
                to_wallet=escrow_wallet,  # La plataforma retiene la comisión
                description=f"Comisión de plataforma del 5% (${platform_fee} USDC) por '{job.title}'",
                released_at=timezone.now(),
                metadata={
                    'total_amount': str(total_amount),
                    'percentage': '5'
                }
            )
            
            return release_transaction, fee_transaction, True, ""
            
        except Exception as e:
            return None, None, False, f"Error al liberar pago final: {str(e)}"
    
    @classmethod
    def refund_to_client(cls, job, bid, reason=''):
        """
        Reembolsa los fondos bloqueados al cliente en caso de cancelación.
        
        Args:
            job: JobOffer a cancelar
            bid: Bid asociada
            reason: Motivo del reembolso
        
        Returns:
            (refund_transactions: list, success: bool, error_msg: str)
        """
        # Buscar todos los depósitos bloqueados
        locked_deposits = cls.objects.filter(
            job=job,
            bid=bid,
            status='LOCKED'
        )
        
        if not locked_deposits.exists():
            return [], False, "No hay fondos bloqueados para reembolsar."
        
        from usuarios.models import Wallet
        escrow_wallet = Wallet.get_escrow_account()
        client_wallet = Wallet.objects.filter(user=job.creator.user).first()
        
        if not client_wallet:
            return [], False, "No se encontró la wallet del cliente."
        
        refund_transactions = []
        
        try:
            for deposit in locked_deposits:
                # Reembolsar del escrow al cliente
                escrow_wallet.restar_saldo(deposit.amount_usdc)
                client_wallet.sumar_saldo(deposit.amount_usdc)
                
                # Actualizar transacción original
                deposit.status = 'REFUNDED'
                deposit.released_at = timezone.now()
                deposit.save()
                
                # Crear registro de reembolso
                refund = cls.objects.create(
                    job=job,
                    bid=bid,
                    amount_usdc=deposit.amount_usdc,
                    transaction_type='REFUND',
                    status='RELEASED',
                    from_wallet=escrow_wallet,
                    to_wallet=client_wallet,
                    description=f"Reembolso de ${deposit.amount_usdc} USDC a {client_wallet.user.get_full_name() or client_wallet.user.username}. Motivo: {reason}",
                    released_at=timezone.now(),
                    metadata={
                        'original_deposit_id': deposit.id,
                        'reason': reason
                    }
                )
                
                refund_transactions.append(refund)
            
            return refund_transactions, True, ""
            
        except Exception as e:
            return [], False, f"Error al procesar reembolso: {str(e)}"

