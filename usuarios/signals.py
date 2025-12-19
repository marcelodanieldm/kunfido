from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from decimal import Decimal
from .models import UserProfile, Wallet


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """
    Señal que crea o actualiza el perfil de usuario automáticamente
    cuando se crea o actualiza un usuario.
    """
    if created:
        UserProfile.objects.create(user=instance)
    else:
        if hasattr(instance, 'profile'):
            instance.profile.save()


@receiver(post_save, sender=User)
def crear_wallet_usuario(sender, instance, created, **kwargs):
    """
    Crea un Wallet automáticamente al crear un User.
    El usuario recibe un saldo inicial de 1000 USDC_MOCK.
    """
    if created:
        Wallet.objects.create(
            user=instance,
            tipo_cuenta='USER',
            balance_usdc=Decimal('1000.00')  # Saldo inicial de demo
        )
