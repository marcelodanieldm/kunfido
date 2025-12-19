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
    
    # Campos adicionales para onboarding
    telefono = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='Teléfono',
        help_text='Número de contacto del usuario'
    )
    
    rubro = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Rubro',
        help_text='Especialidad del profesional (solo para Oficio)'
    )
    
    cuit = models.CharField(
        max_length=13,
        blank=True,
        null=True,
        verbose_name='CUIT/CUIL',
        help_text='CUIT o CUIL del profesional'
    )
    
    matricula = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Matrícula',
        help_text='Matrícula profesional (para administradores de consorcio)'
    )
    
    direccion = models.TextField(
        blank=True,
        null=True,
        verbose_name='Dirección',
        help_text='Dirección del edificio o consorcio'
    )
    
    puntuacion = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)],
        verbose_name='Puntuación',
        help_text='Puntuación del usuario (0.0 - 5.0)'
    )
    
    penalizaciones_acumuladas = models.PositiveIntegerField(
        default=0,
        verbose_name='Penalizaciones Acumuladas',
        help_text='Número de penalizaciones por atrasos no justificados'
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
    
    @property
    def wallet(self):
        """Retorna la wallet del usuario."""
        try:
            from .models import Wallet
            return Wallet.objects.get(user=self.user)
        except:
            return None
    
    def aplicar_penalizacion(self, dias_atraso):
        """
        Aplica penalización por atraso no justificado.
        - Reduce la puntuación según días de atraso
        - Incrementa contador de penalizaciones
        """
        # Calcular reducción de puntuación (0.1 puntos por cada día de atraso, máximo 1.0)
        reduccion = min(dias_atraso * 0.1, 1.0)
        self.puntuacion = max(0.0, self.puntuacion - reduccion)
        
        # Incrementar contador de penalizaciones
        self.penalizaciones_acumuladas += 1
        
        self.save()
        
        return reduccion
    
    @property
    def prioridad_ofertas(self):
        """
        Calcula la prioridad del profesional para aparecer en ofertas.
        Mayor puntuación y menos penalizaciones = mayor prioridad.
        Retorna un score de 0 a 100.
        """
        # Base: puntuación (0-5) convertida a escala 0-50
        score_puntuacion = (self.puntuacion / 5.0) * 50
        
        # Penalización: cada penalización resta 5 puntos (máximo -50)
        penalizacion = min(self.penalizaciones_acumuladas * 5, 50)
        
        # Score final (0-100)
        return max(0, score_puntuacion - penalizacion)


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
        Calcula los días de atraso entre la fecha de entrega pactada y la real.
        Retorna:
            - None si no hay fechas para comparar
            - 0 si se entregó a tiempo o antes
            - Número positivo de días de atraso
        """
        if not self.fecha_entrega_pactada or not self.fecha_entrega_real:
            return None
        
        # Calcular diferencia en días
        delta = self.fecha_entrega_real - self.fecha_entrega_pactada
        dias = delta.days
        
        # Si es negativo o cero, se entregó a tiempo
        return max(0, dias)
    
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
    
    def rechazar_justificacion(self, rechazado_por):
        """
        Rechaza la justificación y aplica penalización al profesional.
        - Reduce puntuación según días de atraso
        - Incrementa contador de penalizaciones
        - Afecta prioridad en futuras ofertas
        """
        from django.utils import timezone
        
        # Obtener perfil del profesional
        perfil = self.profesional.profile
        
        # Aplicar penalización
        reduccion = perfil.aplicar_penalizacion(self.dias_atraso_justificados)
        
        # Marcar como rechazada (penalizacion_omitida permanece False)
        self.fecha_actualizacion = timezone.now()
        self.save()
        
        return reduccion


class Wallet(models.Model):
    """
    Billetera virtual de cada usuario para manejar transacciones internas.
    Usa USDC_MOCK como moneda simulada.
    """
    
    TIPO_CUENTA_CHOICES = [
        ('USER', 'Usuario'),
        ('ESCROW', 'Escrow Plataforma'),
    ]
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='wallet',
        verbose_name='Usuario',
        null=True,
        blank=True,
        help_text='Usuario propietario (null para cuentas del sistema)'
    )
    
    tipo_cuenta = models.CharField(
        max_length=20,
        choices=TIPO_CUENTA_CHOICES,
        default='USER',
        verbose_name='Tipo de Cuenta'
    )
    
    balance_usdc = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        verbose_name='Balance USDC_MOCK',
        help_text='Saldo en USDC_MOCK (moneda simulada)',
        validators=[MinValueValidator(0)]
    )
    
    nombre_cuenta = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Nombre de Cuenta',
        help_text='Nombre descriptivo (ej: Plataforma_Escrow)'
    )
    
    activa = models.BooleanField(
        default=True,
        verbose_name='Cuenta Activa'
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
        verbose_name = 'Billetera'
        verbose_name_plural = 'Billeteras'
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        if self.user:
            return f"Wallet de {self.user.username} - {self.balance_usdc} USDC"
        return f"{self.nombre_cuenta} - {self.balance_usdc} USDC"
    
    def tiene_saldo_suficiente(self, monto):
        """Verifica si la billetera tiene saldo suficiente."""
        return self.balance_usdc >= monto
    
    def restar_saldo(self, monto):
        """Resta monto del saldo. No verifica suficiencia, debe hacerse antes."""
        from decimal import Decimal
        self.balance_usdc -= Decimal(str(monto))
        self.save()
    
    def sumar_saldo(self, monto):
        """Suma monto al saldo."""
        from decimal import Decimal
        self.balance_usdc += Decimal(str(monto))
        self.save()
    
    @classmethod
    def get_escrow_account(cls):
        """Obtiene o crea la cuenta de escrow de la plataforma."""
        escrow, created = cls.objects.get_or_create(
            tipo_cuenta='ESCROW',
            user=None,
            defaults={
                'nombre_cuenta': 'Plataforma_Escrow',
                'balance_usdc': 0.00
            }
        )
        return escrow


class Transaction(models.Model):
    """
    Registro de todas las transacciones financieras en la plataforma.
    Usa DecimalField para precisión financiera.
    """
    
    TIPO_TRANSACCION_CHOICES = [
        ('ESCROW_DEPOSIT', 'Depósito a Escrow'),
        ('ESCROW_RELEASE', 'Liberación de Escrow'),
        ('PAYMENT', 'Pago'),
        ('REFUND', 'Reembolso'),
        ('FEE', 'Comisión Plataforma'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pendiente'),
        ('COMPLETED', 'Completada'),
        ('FAILED', 'Fallida'),
        ('REVERSED', 'Revertida'),
    ]
    
    from_wallet = models.ForeignKey(
        Wallet,
        on_delete=models.PROTECT,
        related_name='transacciones_enviadas',
        verbose_name='Billetera Origen'
    )
    
    to_wallet = models.ForeignKey(
        Wallet,
        on_delete=models.PROTECT,
        related_name='transacciones_recibidas',
        verbose_name='Billetera Destino'
    )
    
    monto_usdc = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='Monto USDC',
        validators=[MinValueValidator(0.01)]
    )
    
    tipo_transaccion = models.CharField(
        max_length=20,
        choices=TIPO_TRANSACCION_CHOICES,
        verbose_name='Tipo de Transacción'
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING',
        verbose_name='Estado'
    )
    
    oferta_relacionada = models.ForeignKey(
        JobOffer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transacciones',
        verbose_name='Oferta Relacionada'
    )
    
    propuesta_relacionada = models.ForeignKey(
        'Proposal',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transacciones',
        verbose_name='Propuesta Relacionada'
    )
    
    descripcion = models.TextField(
        blank=True,
        verbose_name='Descripción',
        help_text='Detalles de la transacción'
    )
    
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Metadata',
        help_text='Datos adicionales en formato JSON'
    )
    
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Transacción'
    )
    
    procesado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transacciones_procesadas',
        verbose_name='Procesado Por'
    )
    
    class Meta:
        verbose_name = 'Transacción'
        verbose_name_plural = 'Transacciones'
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['-fecha_creacion']),
            models.Index(fields=['status']),
            models.Index(fields=['tipo_transaccion']),
        ]
    
    def __str__(self):
        return f"{self.tipo_transaccion} - {self.monto_usdc} USDC - {self.status}"
    
    @classmethod
    def crear_transaccion_escrow(cls, cliente_wallet, monto_total, propuesta, porcentaje_escrow=30):
        """
        Crea una transacción de depósito a escrow cuando se acepta una propuesta.
        
        Parámetros:
        - cliente_wallet: Wallet del cliente
        - monto_total: Monto total de la propuesta
        - propuesta: Instancia de Proposal
        - porcentaje_escrow: Porcentaje a retener (default 30%)
        
        Retorna: (Transaction, monto_escrow) o (None, None) si falla
        """
        from decimal import Decimal, ROUND_HALF_UP
        
        # Calcular monto de escrow (30% del total)
        monto_total_decimal = Decimal(str(monto_total))
        porcentaje_decimal = Decimal(str(porcentaje_escrow)) / Decimal('100')
        monto_escrow = (monto_total_decimal * porcentaje_decimal).quantize(
            Decimal('0.01'), 
            rounding=ROUND_HALF_UP
        )
        
        # Verificar saldo suficiente
        if not cliente_wallet.tiene_saldo_suficiente(monto_escrow):
            return None, None
        
        # Obtener cuenta de escrow
        escrow_wallet = Wallet.get_escrow_account()
        
        # Crear transacción
        transaccion = cls.objects.create(
            from_wallet=cliente_wallet,
            to_wallet=escrow_wallet,
            monto_usdc=monto_escrow,
            tipo_transaccion='ESCROW_DEPOSIT',
            status='PENDING',
            oferta_relacionada=propuesta.oferta,
            propuesta_relacionada=propuesta,
            descripcion=f'Depósito de garantía ({porcentaje_escrow}%) para "{propuesta.oferta.titulo}"',
            metadata={
                'monto_total': str(monto_total_decimal),
                'porcentaje_escrow': porcentaje_escrow,
                'profesional_id': propuesta.profesional.id,
                'cliente_id': cliente_wallet.user.id
            }
        )
        
        # Ejecutar la transacción
        try:
            cliente_wallet.restar_saldo(monto_escrow)
            escrow_wallet.sumar_saldo(monto_escrow)
            transaccion.status = 'COMPLETED'
            transaccion.save()
            
            return transaccion, monto_escrow
        except Exception as e:
            transaccion.status = 'FAILED'
            transaccion.descripcion += f' | Error: {str(e)}'
            transaccion.save()
            return None, None
    
    @classmethod
    def liberar_pago_a_profesional(cls, propuesta, porcentaje_comision=10):
        """
        Libera el pago del escrow al profesional cuando el cliente aprueba el trabajo.
        Cobra una comisión de plataforma (default 10%).
        
        Parámetros:
        - propuesta: Instancia de Proposal
        - porcentaje_comision: Porcentaje de comisión (default 10%)
        
        Retorna: (transaccion_pago, transaccion_comision, monto_liberado) o (None, None, None) si falla
        """
        from decimal import Decimal, ROUND_HALF_UP
        
        # Obtener wallets
        escrow_wallet = Wallet.get_escrow_account()
        profesional_wallet, _ = Wallet.objects.get_or_create(
            user=propuesta.profesional,
            defaults={'tipo_cuenta': 'USER', 'balance_usdc': Decimal('1000.00')}
        )
        
        # Obtener transacción de escrow original
        transaccion_escrow = cls.objects.filter(
            propuesta_relacionada=propuesta,
            tipo_transaccion='ESCROW_DEPOSIT',
            status='COMPLETED'
        ).first()
        
        if not transaccion_escrow:
            return None, None, None
        
        # Calcular montos
        monto_total = Decimal(str(propuesta.monto))
        monto_escrow = transaccion_escrow.monto_usdc  # 30% que está en escrow
        
        # Calcular comisión sobre el monto total (10%)
        porcentaje_comision_decimal = Decimal(str(porcentaje_comision)) / Decimal('100')
        monto_comision = (monto_total * porcentaje_comision_decimal).quantize(
            Decimal('0.01'),
            rounding=ROUND_HALF_UP
        )
        
        # El monto que recibe el profesional es: 70% restante + 30% escrow - comisión total
        # Para simplificar: liberamos todo el escrow menos la comisión proporcional del escrow
        comision_del_escrow = (monto_escrow * porcentaje_comision_decimal / Decimal('0.30')).quantize(
            Decimal('0.01'),
            rounding=ROUND_HALF_UP
        )
        
        monto_neto_profesional = monto_escrow - comision_del_escrow
        
        # Verificar saldo en escrow
        if not escrow_wallet.tiene_saldo_suficiente(monto_escrow):
            return None, None, None
        
        try:
            # 1. Crear transacción de liberación de pago al profesional
            transaccion_pago = cls.objects.create(
                from_wallet=escrow_wallet,
                to_wallet=profesional_wallet,
                monto_usdc=monto_neto_profesional,
                tipo_transaccion='RELEASE_PAYMENT',
                status='PENDING',
                oferta_relacionada=propuesta.oferta,
                propuesta_relacionada=propuesta,
                descripcion=f'Pago liberado a {propuesta.profesional.get_full_name() or propuesta.profesional.username} por "{propuesta.oferta.titulo}"',
                metadata={
                    'monto_total': str(monto_total),
                    'monto_escrow': str(monto_escrow),
                    'comision': str(comision_del_escrow),
                    'porcentaje_comision': porcentaje_comision
                }
            )
            
            # 2. Crear transacción de comisión para la plataforma
            plataforma_wallet = Wallet.get_escrow_account()  # Usamos la misma cuenta de escrow
            transaccion_comision = cls.objects.create(
                from_wallet=escrow_wallet,
                to_wallet=plataforma_wallet,
                monto_usdc=comision_del_escrow,
                tipo_transaccion='FEE',
                status='PENDING',
                oferta_relacionada=propuesta.oferta,
                propuesta_relacionada=propuesta,
                descripcion=f'Comisión de plataforma ({porcentaje_comision}%) por "{propuesta.oferta.titulo}"',
                metadata={
                    'monto_total': str(monto_total),
                    'porcentaje': porcentaje_comision
                }
            )
            
            # 3. Ejecutar transferencias
            escrow_wallet.restar_saldo(monto_escrow)  # Restar todo el escrow
            profesional_wallet.sumar_saldo(monto_neto_profesional)  # Dar al profesional su parte
            # La comisión ya queda en el escrow (no se mueve físicamente)
            
            # Marcar transacciones como completadas
            transaccion_pago.status = 'COMPLETED'
            transaccion_pago.save()
            transaccion_comision.status = 'COMPLETED'
            transaccion_comision.save()
            
            return transaccion_pago, transaccion_comision, monto_neto_profesional
            
        except Exception as e:
            if 'transaccion_pago' in locals():
                transaccion_pago.status = 'FAILED'
                transaccion_pago.descripcion += f' | Error: {str(e)}'
                transaccion_pago.save()
            if 'transaccion_comision' in locals():
                transaccion_comision.status = 'FAILED'
                transaccion_comision.save()
            return None, None, None
    
    @classmethod
    def procesar_reembolso(cls, propuesta, motivo=''):
        """
        Procesa un reembolso devolviendo el monto de escrow al cliente.
        
        Parámetros:
        - propuesta: Instancia de Proposal
        - motivo: Razón del reembolso
        
        Retorna: (Transaction, monto_reembolsado) o (None, None) si falla
        """
        from decimal import Decimal
        
        # Obtener wallets
        escrow_wallet = Wallet.get_escrow_account()
        cliente_wallet, _ = Wallet.objects.get_or_create(
            user=propuesta.oferta.creador,
            defaults={'tipo_cuenta': 'USER', 'balance_usdc': Decimal('1000.00')}
        )
        
        # Obtener transacción de escrow original
        transaccion_escrow = cls.objects.filter(
            propuesta_relacionada=propuesta,
            tipo_transaccion='ESCROW_DEPOSIT',
            status='COMPLETED'
        ).first()
        
        if not transaccion_escrow:
            return None, None
        
        monto_reembolso = transaccion_escrow.monto_usdc
        
        # Verificar saldo en escrow
        if not escrow_wallet.tiene_saldo_suficiente(monto_reembolso):
            return None, None
        
        try:
            # Crear transacción de reembolso
            transaccion_reembolso = cls.objects.create(
                from_wallet=escrow_wallet,
                to_wallet=cliente_wallet,
                monto_usdc=monto_reembolso,
                tipo_transaccion='REFUND',
                status='PENDING',
                oferta_relacionada=propuesta.oferta,
                propuesta_relacionada=propuesta,
                descripcion=f'Reembolso a {cliente_wallet.user.get_full_name() or cliente_wallet.user.username}. Motivo: {motivo}',
                metadata={
                    'motivo': motivo,
                    'transaccion_original_id': transaccion_escrow.id
                }
            )
            
            # Ejecutar transferencia
            escrow_wallet.restar_saldo(monto_reembolso)
            cliente_wallet.sumar_saldo(monto_reembolso)
            
            transaccion_reembolso.status = 'COMPLETED'
            transaccion_reembolso.save()
            
            return transaccion_reembolso, monto_reembolso
            
        except Exception as e:
            if 'transaccion_reembolso' in locals():
                transaccion_reembolso.status = 'FAILED'
                transaccion_reembolso.descripcion += f' | Error: {str(e)}'
                transaccion_reembolso.save()
            return None, None


class WorkEvent(models.Model):
    """
    Registro de eventos importantes en el ciclo de vida de un trabajo.
    """
    
    TIPO_EVENTO_CHOICES = [
        ('TRABAJO_INICIADO', 'Trabajo Iniciado'),
        ('TRABAJO_PAUSADO', 'Trabajo Pausado'),
        ('TRABAJO_REANUDADO', 'Trabajo Reanudado'),
        ('TRABAJO_COMPLETADO', 'Trabajo Completado'),
        ('TRABAJO_CANCELADO', 'Trabajo Cancelado'),
        ('PAGO_ESCROW', 'Pago Depositado en Escrow'),
        ('PAGO_LIBERADO', 'Pago Liberado al Profesional'),
        ('ATRASO_JUSTIFICADO', 'Atraso Justificado'),
        ('JUSTIFICACION_ACEPTADA', 'Justificación Aceptada'),
    ]
    
    oferta = models.ForeignKey(
        JobOffer,
        on_delete=models.CASCADE,
        related_name='eventos',
        verbose_name='Oferta de Trabajo'
    )
    
    tipo_evento = models.CharField(
        max_length=30,
        choices=TIPO_EVENTO_CHOICES,
        verbose_name='Tipo de Evento'
    )
    
    descripcion = models.TextField(
        verbose_name='Descripción',
        help_text='Detalles del evento'
    )
    
    usuario_relacionado = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='eventos_generados',
        verbose_name='Usuario Relacionado'
    )
    
    transaccion_relacionada = models.ForeignKey(
        Transaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='eventos',
        verbose_name='Transacción Relacionada'
    )
    
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Metadata',
        help_text='Datos adicionales del evento'
    )
    
    fecha_evento = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha del Evento'
    )
    
    class Meta:
        verbose_name = 'Evento de Trabajo'
        verbose_name_plural = 'Eventos de Trabajos'
        ordering = ['-fecha_evento']
        indexes = [
            models.Index(fields=['-fecha_evento']),
            models.Index(fields=['tipo_evento']),
        ]
    
    def __str__(self):
        return f"{self.get_tipo_evento_display()} - {self.oferta.titulo} - {self.fecha_evento.strftime('%d/%m/%Y %H:%M')}"
    
    @classmethod
    def crear_evento_trabajo_iniciado(cls, oferta, propuesta, transaccion):
        """
        Crea un evento de 'Trabajo Iniciado' cuando se acepta una propuesta y se procesa el pago.
        """
        return cls.objects.create(
            oferta=oferta,
            tipo_evento='TRABAJO_INICIADO',
            descripcion=f'Trabajo iniciado con el profesional {propuesta.profesional.get_full_name() or propuesta.profesional.username}. '
                       f'Monto acordado: ${propuesta.monto} ARS. Días estimados: {propuesta.dias_entrega}.',
            usuario_relacionado=propuesta.profesional,
            transaccion_relacionada=transaccion,
            metadata={
                'propuesta_id': propuesta.id,
                'profesional_id': propuesta.profesional.id,
                'monto_acordado': str(propuesta.monto),
                'dias_entrega': propuesta.dias_entrega,
                'version_propuesta': propuesta.version
            }
        )
    
    @classmethod
    def crear_evento_trabajo_completado(cls, oferta, propuesta, transaccion_pago, transaccion_comision):
        """
        Crea un evento de 'Trabajo Completado' cuando el cliente aprueba la entrega.
        """
        return cls.objects.create(
            oferta=oferta,
            tipo_evento='TRABAJO_COMPLETADO',
            descripcion=f'Trabajo completado y aprobado por {oferta.creador.get_full_name() or oferta.creador.username}. '
                       f'Pago de ${transaccion_pago.monto_usdc} USDC liberado a {propuesta.profesional.get_full_name() or propuesta.profesional.username}.',
            usuario_relacionado=oferta.creador,
            transaccion_relacionada=transaccion_pago,
            metadata={
                'propuesta_id': propuesta.id,
                'monto_pagado': str(transaccion_pago.monto_usdc),
                'comision': str(transaccion_comision.monto_usdc) if transaccion_comision else '0',
                'fecha_aprobacion': timezone.now().isoformat()
            }
        )
    
    @classmethod
    def crear_evento_reembolso(cls, oferta, propuesta, transaccion_reembolso, motivo):
        """
        Crea un evento de reembolso cuando se devuelve el dinero al cliente.
        """
        return cls.objects.create(
            oferta=oferta,
            tipo_evento='TRABAJO_CANCELADO',
            descripcion=f'Trabajo cancelado. Reembolso de ${transaccion_reembolso.monto_usdc} USDC procesado. Motivo: {motivo}',
            usuario_relacionado=oferta.creador,
            transaccion_relacionada=transaccion_reembolso,
            metadata={
                'propuesta_id': propuesta.id,
                'monto_reembolsado': str(transaccion_reembolso.monto_usdc),
                'motivo': motivo,
                'fecha_reembolso': timezone.now().isoformat()
            }
        )
