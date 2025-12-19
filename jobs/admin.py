from django.contrib import admin
from .models import JobOffer, Bid, Vote


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
        'created_at',
    ]
    
    list_filter = [
        'status',
        'is_consorcio',
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
            'fields': ('status', 'is_consorcio')
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

