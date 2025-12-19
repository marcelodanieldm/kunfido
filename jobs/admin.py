from django.contrib import admin
from .models import JobOffer, Bid, Vote, DelayRegistry, EscrowTransaction


@admin.register(JobOffer)
class JobOfferAdmin(admin.ModelAdmin):
    """
    Administración de Ofertas de Trabajo.
    """
    list_display = [
        'id',
        'title',
        'creator',
        'budget_base_ars',
        'budget_base_usdc',
        'status',
        'is_consorcio',
        'is_delayed',
        'created_at',
    ]
    
    list_filter = [
        'status',
        'is_consorcio',
        'is_delayed',
        'created_at',
    ]
    
    search_fields = [
        'title',
        'description',
        'creator__user__username',
        'creator__user__email',
    ]
    
    readonly_fields = [
        'budget_base_usdc',
        'is_delayed',
        'created_at',
        'updated_at',
    ]
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('creator', 'title', 'description')
        }),
        ('Presupuesto', {
            'fields': ('budget_base_ars', 'budget_base_usdc')
        }),
        ('Estado', {
            'fields': ('status', 'is_consorcio', 'is_delayed')
        }),
        ('Fechas de Trabajo', {
            'fields': ('start_confirmed_date', 'expected_completion_date'),
            'description': 'Fechas relacionadas con el inicio y finalización del trabajo'
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def budget_base_usdc(self, obj):
        """Muestra el presupuesto en USDC."""
        return f"${obj.budget_base_usdc} USDC"
    budget_base_usdc.short_description = 'Presupuesto Base (USDC)'


@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    """
    Administración de Pujas.
    """
    list_display = [
        'id',
        'job_offer',
        'professional',
        'amount_ars',
        'amount_usdc_display',
        'estimated_days',
        'total_votes',
        'is_active',
        'is_winner',
        'created_at',
    ]
    
    list_filter = [
        'is_active',
        'is_winner',
        'created_at',
    ]
    
    search_fields = [
        'job_offer__title',
        'professional__user__username',
        'professional__user__email',
        'pitch_text',
    ]
    
    readonly_fields = [
        'amount_usdc_display',
        'total_votes',
        'created_at',
        'updated_at',
    ]
    
    fieldsets = (
        ('Relaciones', {
            'fields': ('job_offer', 'professional')
        }),
        ('Propuesta', {
            'fields': ('amount_ars', 'amount_usdc_display', 'estimated_days', 'pitch_text')
        }),
        ('Estado', {
            'fields': ('is_active', 'is_winner', 'total_votes')
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_winner', 'mark_as_inactive']
    
    def amount_usdc_display(self, obj):
        """Muestra el monto en USDC."""
        return f"${obj.amount_usdc} USDC"
    amount_usdc_display.short_description = 'Monto (USDC)'
    
    def mark_as_winner(self, request, queryset):
        """Marca las pujas seleccionadas como ganadoras."""
        for bid in queryset:
            bid.mark_as_winner()
        self.message_user(request, f"{queryset.count()} puja(s) marcada(s) como ganadora(s).")
    mark_as_winner.short_description = "Marcar como ganadora"
    
    def mark_as_inactive(self, request, queryset):
        """Marca las pujas seleccionadas como inactivas."""
        count = queryset.update(is_active=False)
        self.message_user(request, f"{count} puja(s) marcada(s) como inactiva(s).")
    mark_as_inactive.short_description = "Marcar como inactiva"


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    """
    Administración de Votos.
    """
    list_display = [
        'id',
        'user',
        'bid',
        'bid_job_offer',
        'created_at',
    ]
    
    list_filter = [
        'created_at',
    ]
    
    search_fields = [
        'user__username',
        'user__email',
        'bid__job_offer__title',
    ]
    
    readonly_fields = [
        'created_at',
    ]
    
    def bid_job_offer(self, obj):
        """Muestra la oferta de trabajo asociada a la puja."""
        return obj.bid.job_offer.title
    bid_job_offer.short_description = 'Oferta de Trabajo'
    
    # No permitir edición, solo lectura
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(DelayRegistry)
class DelayRegistryAdmin(admin.ModelAdmin):
    """
    Administración de Registros de Atrasos.
    """
    list_display = [
        'id',
        'bid_job_offer',
        'professional_name',
        'days_delayed',
        'status',
        'accepted_by_client',
        'penalty_applied',
        'created_at',
        'reviewed_at',
    ]
    
    list_filter = [
        'status',
        'accepted_by_client',
        'penalty_applied',
        'created_at',
        'reviewed_at',
    ]
    
    search_fields = [
        'bid__job_offer__title',
        'bid__professional__user__username',
        'bid__professional__user__email',
        'reason',
    ]
    
    readonly_fields = [
        'bid',
        'days_delayed',
        'created_at',
        'reviewed_at',
        'reviewed_by',
    ]
    
    fieldsets = (
        ('Información del Atraso', {
            'fields': ('bid', 'days_delayed', 'reason')
        }),
        ('Estado y Revisión', {
            'fields': ('status', 'accepted_by_client', 'penalty_applied')
        }),
        ('Metadatos', {
            'fields': ('created_at', 'reviewed_at', 'reviewed_by'),
            'classes': ('collapse',)
        }),
    )
    
    def bid_job_offer(self, obj):
        """Muestra la oferta de trabajo asociada."""
        return obj.bid.job_offer.title
    bid_job_offer.short_description = 'Oferta de Trabajo'
    
    def professional_name(self, obj):
        """Muestra el nombre del profesional."""
        return obj.bid.professional.nombre_completo
    professional_name.short_description = 'Profesional'
    
    # No permitir creación manual
    def has_add_permission(self, request):
        return False


@admin.register(EscrowTransaction)
class EscrowTransactionAdmin(admin.ModelAdmin):
    """
    Administración de Transacciones de Escrow.
    """
    list_display = [
        'id',
        'job_title',
        'transaction_type',
        'amount_usdc',
        'status',
        'from_wallet_display',
        'to_wallet_display',
        'created_at',
        'released_at',
    ]
    
    list_filter = [
        'status',
        'transaction_type',
        'created_at',
        'released_at',
    ]
    
    search_fields = [
        'job__title',
        'bid__professional__user__username',
        'description',
    ]
    
    readonly_fields = [
        'job',
        'bid',
        'amount_usdc',
        'transaction_type',
        'status',
        'from_wallet',
        'to_wallet',
        'description',
        'metadata',
        'created_at',
        'updated_at',
        'released_at',
    ]
    
    fieldsets = (
        ('Información de la Transacción', {
            'fields': ('job', 'bid', 'transaction_type', 'amount_usdc', 'status')
        }),
        ('Wallets Involucradas', {
            'fields': ('from_wallet', 'to_wallet')
        }),
        ('Detalles', {
            'fields': ('description', 'metadata')
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at', 'released_at'),
            'classes': ('collapse',)
        }),
    )
    
    def job_title(self, obj):
        """Muestra el título del trabajo."""
        return obj.job.title
    job_title.short_description = 'Trabajo'
    
    def from_wallet_display(self, obj):
        """Muestra la wallet de origen."""
        if obj.from_wallet and obj.from_wallet.user:
            return f"{obj.from_wallet.user.username} (${obj.from_wallet.balance_usdc} USDC)"
        elif obj.from_wallet:
            return f"{obj.from_wallet.nombre_cuenta} (${obj.from_wallet.balance_usdc} USDC)"
        return "N/A"
    from_wallet_display.short_description = 'Wallet Origen'
    
    def to_wallet_display(self, obj):
        """Muestra la wallet de destino."""
        if obj.to_wallet and obj.to_wallet.user:
            return f"{obj.to_wallet.user.username} (${obj.to_wallet.balance_usdc} USDC)"
        elif obj.to_wallet:
            return f"{obj.to_wallet.nombre_cuenta} (${obj.to_wallet.balance_usdc} USDC)"
        return "N/A"
    to_wallet_display.short_description = 'Wallet Destino'
    
    # No permitir creación ni edición manual (solo lectura)
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False

