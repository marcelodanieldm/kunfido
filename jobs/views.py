from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Avg
from django.core.paginator import Paginator
from django.utils import timezone
from .models import JobOffer, Bid, Vote, DelayRegistry, EscrowTransaction
from usuarios.models import Wallet
from decimal import Decimal


def job_list(request):
    """Vista para listar todas las ofertas de trabajo con filtros."""
    jobs = JobOffer.objects.all()
    
    # Filtro por estado
    status = request.GET.get('status', '')
    if status:
        jobs = jobs.filter(status=status)
    
    # Filtro por búsqueda
    search = request.GET.get('search', '')
    if search:
        jobs = jobs.filter(
            Q(title__icontains=search) | 
            Q(description__icontains=search)
        )
    
    # Paginación
    paginator = Paginator(jobs, 10)  # 10 ofertas por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'jobs': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
    }
    
    return render(request, 'jobs/job_list.html', context)


def job_detail(request, job_id):
    """Vista para mostrar el detalle de una oferta de trabajo."""
    job = get_object_or_404(JobOffer, id=job_id)
    bids = job.get_active_bids()
    
    # Verificar estado de deadline si está en progreso
    if job.status == 'IN_PROGRESS':
        job.check_deadline_status()
    
    # Verificar si el usuario es el dueño
    is_owner = False
    if request.user.is_authenticated and hasattr(request.user, 'profile'):
        is_owner = job.creator == request.user.profile
    
    # Verificar si el usuario es OFICIO
    is_oficio = False
    user_bid = None
    if request.user.is_authenticated and hasattr(request.user, 'profile'):
        is_oficio = request.user.profile.tipo_rol == 'OFICIO'
        if is_oficio:
            # Buscar si el usuario ya tiene una propuesta
            user_bid = bids.filter(professional=request.user.profile).first()
    
    # Calcular promedio de ofertas
    avg_bid_amount = bids.aggregate(Avg('amount_ars'))['amount_ars__avg'] or 0
    
    # Obtener registros de atraso pendientes (para el cliente)
    pending_delays = None
    if is_owner:
        pending_delays = DelayRegistry.get_pending_for_job(job)
    
    # Verificar estado de transacciones de escrow
    initial_release_exists = EscrowTransaction.objects.filter(
        job=job,
        transaction_type='INITIAL_RELEASE',
        status='RELEASED'
    ).exists()
    
    final_release_exists = EscrowTransaction.objects.filter(
        job=job,
        transaction_type='FINAL_RELEASE',
        status='RELEASED'
    ).exists()
    
    context = {
        'job': job,
        'bids': bids,
        'is_owner': is_owner,
        'is_oficio': is_oficio,
        'user_bid': user_bid,
        'avg_bid_amount': avg_bid_amount,
        'pending_delays': pending_delays,
        'initial_release_exists': initial_release_exists,
        'final_release_exists': final_release_exists,
    }
    
    return render(request, 'jobs/job_detail.html', context)


@login_required
def submit_bid(request, job_id):
    """Vista para enviar o actualizar una propuesta."""
    if request.method != 'POST':
        return redirect('job_detail', job_id=job_id)
    
    job = get_object_or_404(JobOffer, id=job_id)
    
    # Verificar que el usuario sea OFICIO
    if not hasattr(request.user, 'profile') or request.user.profile.tipo_rol != 'OFICIO':
        messages.error(request, 'Solo los usuarios de tipo OFICIO pueden enviar propuestas.')
        return redirect('job_detail', job_id=job_id)
    
    # Verificar que la oferta esté abierta
    if job.status != 'OPEN':
        messages.error(request, 'Esta oferta ya no acepta propuestas.')
        return redirect('job_detail', job_id=job_id)
    
    # Obtener datos del formulario
    amount_ars = request.POST.get('amount_ars')
    estimated_days = request.POST.get('estimated_days')
    pitch_text = request.POST.get('pitch_text')
    
    # Validar datos
    try:
        amount_ars = Decimal(amount_ars)
        estimated_days = int(estimated_days)
        
        if amount_ars <= 0:
            raise ValueError("El monto debe ser mayor a 0")
        if estimated_days <= 0:
            raise ValueError("Los días estimados deben ser mayor a 0")
        if not pitch_text or len(pitch_text.strip()) < 20:
            raise ValueError("La propuesta debe tener al menos 20 caracteres")
            
    except (ValueError, TypeError) as e:
        messages.error(request, f'Error en los datos: {str(e)}')
        return redirect('job_detail', job_id=job_id)
    
    # Buscar si ya existe una propuesta del usuario
    existing_bid = Bid.objects.filter(
        job_offer=job,
        professional=request.user.profile,
        is_active=True
    ).first()
    
    if existing_bid:
        # Actualizar propuesta existente
        existing_bid.amount_ars = amount_ars
        existing_bid.estimated_days = estimated_days
        existing_bid.pitch_text = pitch_text
        existing_bid.save()
        messages.success(request, '¡Tu propuesta ha sido actualizada exitosamente!')
    else:
        # Crear nueva propuesta
        Bid.objects.create(
            job_offer=job,
            professional=request.user.profile,
            amount_ars=amount_ars,
            estimated_days=estimated_days,
            pitch_text=pitch_text
        )
        messages.success(request, '¡Tu propuesta ha sido enviada exitosamente!')
    
    return redirect('job_detail', job_id=job_id)


@login_required
def accept_bid(request, bid_id):
    """Vista para aceptar una propuesta con verificación de saldo y bloqueo de fondos."""
    if request.method != 'POST':
        return redirect('job_list')
    
    bid = get_object_or_404(Bid, id=bid_id)
    job = bid.job_offer
    
    # Verificar que el usuario sea el dueño de la oferta
    if not hasattr(request.user, 'profile') or job.creator != request.user.profile:
        messages.error(request, 'No tienes permiso para aceptar esta propuesta.')
        return redirect('job_detail', job_id=job.id)
    
    # Verificar que la oferta esté abierta
    if job.status != 'OPEN':
        messages.error(request, 'Esta oferta ya no acepta cambios.')
        return redirect('job_detail', job_id=job.id)
    
    # Obtener o crear wallet del cliente
    client_wallet, created = Wallet.objects.get_or_create(
        user=request.user,
        defaults={'tipo_cuenta': 'USER', 'balance_usdc': Decimal('0.00')}
    )
    
    # Bloquear el 30% inicial en escrow
    transaction, success, error_msg = EscrowTransaction.lock_initial_deposit(
        job=job,
        bid=bid,
        client_wallet=client_wallet
    )
    
    if not success:
        # Si no tiene saldo suficiente, redirigir a cargar fondos
        messages.error(
            request,
            f'{error_msg} Necesita ${bid.amount_usdc * Decimal("0.30")} USDC para aceptar esta propuesta.'
        )
        # Redirigir a la página de wallet para cargar fondos
        return redirect('wallet')  # Asumiendo que tienes una vista 'wallet'
    
    # Marcar la propuesta como ganadora (esto cambia status a IN_PROGRESS)
    bid.mark_as_winner()
    
    messages.success(
        request,
        f'¡Propuesta de {bid.professional.nombre_completo} aceptada! '
        f'Se han bloqueado ${transaction.amount_usdc} USDC (30% del total) en garantía. '
        'Confirme el inicio de obra para liberar el pago al profesional.'
    )
    
    return redirect('job_detail', job_id=job.id)


@login_required
def edit_job(request, job_id):
    """Vista placeholder para editar una oferta de trabajo."""
    job = get_object_or_404(JobOffer, id=job_id)
    
    # Verificar que el usuario sea el dueño
    if not hasattr(request.user, 'profile') or job.creator != request.user.profile:
        messages.error(request, 'No tienes permiso para editar esta oferta.')
        return redirect('job_detail', job_id=job_id)
    
    messages.info(request, 'La funcionalidad de edición está en desarrollo.')
    return redirect('job_detail', job_id=job_id)


@login_required
def submit_delay_justification(request, job_id):
    """
    Vista para que el profesional (OFICIO) envíe una justificación de atraso.
    Implementa el 'Derecho a Réplica'.
    """
    job = get_object_or_404(JobOffer, id=job_id)
    
    # Verificar que el usuario sea OFICIO
    if not hasattr(request.user, 'profile') or request.user.profile.tipo_rol != 'OFICIO':
        messages.error(request, 'Solo los profesionales pueden enviar justificaciones.')
        return redirect('job_detail', job_id=job_id)
    
    # Obtener la propuesta ganadora del profesional
    bid = job.get_winning_bid()
    if not bid or bid.professional != request.user.profile:
        messages.error(request, 'No tienes una propuesta aceptada en esta oferta.')
        return redirect('job_detail', job_id=job_id)
    
    # Verificar que el trabajo esté en progreso
    if job.status != 'IN_PROGRESS':
        messages.error(request, 'Solo se pueden justificar atrasos en trabajos en progreso.')
        return redirect('job_detail', job_id=job_id)
    
    # Verificar que realmente haya un atraso
    job.check_deadline_status()
    if not job.is_delayed:
        messages.info(request, 'El trabajo no tiene atrasos registrados.')
        return redirect('job_detail', job_id=job_id)
    
    if request.method == 'POST':
        reason = request.POST.get('reason', '').strip()
        
        if not reason or len(reason) < 50:
            messages.error(request, 'La justificación debe tener al menos 50 caracteres.')
            return render(request, 'jobs/delay_justification_form.html', {
                'job': job,
                'bid': bid,
                'days_delayed': job.get_days_delayed()
            })
        
        # Crear el registro de atraso
        delay_registry = DelayRegistry.create_delay_report(bid, reason)
        
        messages.success(
            request, 
            f'Tu justificación ha sido enviada. El cliente tiene {job.get_days_delayed()} días de atraso registrados. '
            'Esperando revisión del cliente.'
        )
        return redirect('job_detail', job_id=job_id)
    
    # GET: Mostrar formulario
    # Verificar si ya existe una justificación pendiente
    existing_pending = DelayRegistry.objects.filter(
        bid=bid,
        status='PENDING'
    ).first()
    
    context = {
        'job': job,
        'bid': bid,
        'days_delayed': job.get_days_delayed(),
        'existing_justification': existing_pending,
    }
    
    return render(request, 'jobs/delay_justification_form.html', context)


@login_required
def review_delay_justification(request, delay_id):
    """
    Vista para que el cliente revise y acepte/rechace una justificación de atraso.
    """
    delay_registry = get_object_or_404(DelayRegistry, id=delay_id)
    job = delay_registry.bid.job_offer
    
    # Verificar que el usuario sea el dueño de la oferta
    if not hasattr(request.user, 'profile') or job.creator != request.user.profile:
        messages.error(request, 'No tienes permiso para revisar esta justificación.')
        return redirect('job_detail', job_id=job.id)
    
    # Verificar que la justificación esté pendiente
    if delay_registry.status != 'PENDING':
        messages.info(request, 'Esta justificación ya fue revisada.')
        return redirect('job_detail', job_id=job.id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'accept':
            delay_registry.accept_delay(request.user)
            messages.success(
                request,
                f'Has aceptado la justificación de {delay_registry.bid.professional.nombre_completo}. '
                'No se aplicará penalización por este atraso.'
            )
        elif action == 'reject':
            delay_registry.reject_delay(request.user)
            messages.warning(
                request,
                f'Has rechazado la justificación. Se aplicará la penalización correspondiente a '
                f'{delay_registry.bid.professional.nombre_completo}.'
            )
        else:
            messages.error(request, 'Acción no válida.')
        
        return redirect('job_detail', job_id=job.id)
    
    # GET: Mostrar página de revisión
    context = {
        'delay_registry': delay_registry,
        'job': job,
        'bid': delay_registry.bid,
    }
    
    return render(request, 'jobs/review_delay_justification.html', context)


@login_required
def delay_registries_list(request):
    """
    Vista para listar todos los registros de atraso.
    - Para OFICIO: sus propios registros
    - Para PERSONA/CONSORCIO: registros de sus ofertas
    """
    if not hasattr(request.user, 'profile'):
        messages.error(request, 'Perfil de usuario no encontrado.')
        return redirect('home')
    
    profile = request.user.profile
    
    if profile.tipo_rol == 'OFICIO':
        # Mostrar registros donde el usuario es el profesional
        delay_registries = DelayRegistry.objects.filter(
            bid__professional=profile
        ).select_related(
            'bid__job_offer',
            'bid__professional__user',
            'reviewed_by'
        ).order_by('-created_at')
    else:
        # Mostrar registros de ofertas creadas por el usuario
        delay_registries = DelayRegistry.objects.filter(
            bid__job_offer__creator=profile
        ).select_related(
            'bid__job_offer',
            'bid__professional__user',
            'reviewed_by'
        ).order_by('-created_at')
    
    # Filtro por estado
    status_filter = request.GET.get('status', '')
    if status_filter:
        delay_registries = delay_registries.filter(status=status_filter)
    
    # Paginación
    paginator = Paginator(delay_registries, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'delay_registries': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'user_role': profile.tipo_rol,
    }
    
    return render(request, 'jobs/delay_registries_list.html', context)


def job_tracking(request, job_id):
    """
    Vista de seguimiento detallado de un trabajo en progreso.
    Muestra barra de tiempo dinámica, alertas de atraso y acciones disponibles.
    """
    job = get_object_or_404(JobOffer, id=job_id)
    
    # Verificar estado de atraso
    if job.status == 'IN_PROGRESS':
        job.check_deadline_status()
    
    # Verificar permisos
    is_owner = False
    is_oficio = False
    winning_bid = None
    
    if request.user.is_authenticated and hasattr(request.user, 'profile'):
        is_owner = job.creator == request.user.profile
        winning_bid = job.get_winning_bid()
        
        if winning_bid:
            is_oficio = winning_bid.professional == request.user.profile
    
    # Si no hay propuesta ganadora, redirigir al detalle
    if not winning_bid:
        messages.info(request, 'Este trabajo aún no tiene un profesional asignado.')
        return redirect('job_detail', job_id=job_id)
    
    # Calcular métricas de tiempo
    from datetime import timedelta
    from django.utils import timezone
    
    now = timezone.now()
    start_date = job.start_confirmed_date
    expected_date = job.expected_completion_date
    
    # Días transcurridos
    elapsed_days = (now - start_date).days if start_date else 0
    
    # Días estimados
    estimated_days = winning_bid.estimated_days
    
    # Días restantes (negativos si está atrasado)
    if expected_date:
        remaining_delta = expected_date - now
        remaining_days = remaining_delta.days
        hours_until_deadline = int(remaining_delta.total_seconds() / 3600)
    else:
        remaining_days = estimated_days - elapsed_days
        hours_until_deadline = remaining_days * 24
    
    # Porcentaje de progreso
    if estimated_days > 0:
        progress_percentage = min((elapsed_days / estimated_days) * 100, 100)
    else:
        progress_percentage = 0
    
    # Determinar estado del tiempo
    days_delayed = 0
    if job.is_delayed:
        time_status = 'delayed'
        days_delayed = job.get_days_delayed()
        remaining_label = 'de Atraso'
    elif hours_until_deadline <= 24 and hours_until_deadline > 0:
        time_status = 'warning'
        remaining_label = 'Restantes'
    else:
        time_status = 'on-time'
        remaining_label = 'Restantes'
    
    # Obtener justificaciones
    delay_registries = DelayRegistry.objects.filter(
        bid=winning_bid
    ).order_by('-created_at')
    
    # Verificar si hay justificación pendiente
    pending_justification = delay_registries.filter(status='PENDING').first()
    has_pending_justification = pending_justification is not None
    
    context = {
        'job': job,
        'winning_bid': winning_bid,
        'is_owner': is_owner,
        'is_oficio': is_oficio,
        'time_status': time_status,
        'progress_percentage': progress_percentage,
        'elapsed_days': elapsed_days,
        'estimated_days': estimated_days,
        'remaining_days': abs(remaining_days),
        'remaining_label': remaining_label,
        'hours_until_deadline': abs(hours_until_deadline),
        'days_delayed': days_delayed,
        'delay_registries': delay_registries,
        'pending_justification': pending_justification,
        'has_pending_justification': has_pending_justification,
    }
    
    return render(request, 'jobs/job_tracking.html', context)


@login_required
def confirm_work_start(request, job_id):
    """
    Vista para que el cliente confirme el inicio de obra.
    Esto libera el 30% inicial al profesional y bloquea el 70% restante.
    """
    if request.method != 'POST':
        return redirect('job_detail', job_id=job_id)
    
    job = get_object_or_404(JobOffer, id=job_id)
    
    # Verificar que el usuario sea el dueño
    if not hasattr(request.user, 'profile') or job.creator != request.user.profile:
        messages.error(request, 'No tienes permiso para confirmar el inicio de obra.')
        return redirect('job_detail', job_id=job_id)
    
    # Verificar que el trabajo esté en progreso
    if job.status != 'IN_PROGRESS':
        messages.error(request, 'El trabajo no está en progreso.')
        return redirect('job_detail', job_id=job_id)
    
    winning_bid = job.get_winning_bid()
    if not winning_bid:
        messages.error(request, 'No hay propuesta ganadora.')
        return redirect('job_detail', job_id=job_id)
    
    # Verificar si ya se confirmó el inicio
    already_released = EscrowTransaction.objects.filter(
        job=job,
        transaction_type='INITIAL_RELEASE',
        status='RELEASED'
    ).exists()
    
    if already_released:
        messages.info(request, 'El inicio de obra ya fue confirmado anteriormente.')
        return redirect('job_detail', job_id=job_id)
    
    # Liberar el 30% inicial
    release_transaction, success, error_msg = EscrowTransaction.release_initial_payment(
        job=job,
        bid=winning_bid
    )
    
    if not success:
        messages.error(request, f'Error al liberar el pago: {error_msg}')
        return redirect('job_detail', job_id=job_id)
    
    # Bloquear el 70% restante
    client_wallet = Wallet.objects.filter(user=request.user).first()
    if not client_wallet:
        messages.error(request, 'No se encontró su wallet.')
        return redirect('job_detail', job_id=job_id)
    
    remaining_transaction, success_remaining, error_remaining = EscrowTransaction.lock_remaining_amount(
        job=job,
        bid=winning_bid,
        client_wallet=client_wallet
    )
    
    if not success_remaining:
        messages.error(
            request,
            f'Se liberó el 30% inicial, pero no se pudo bloquear el 70% restante: {error_remaining}'
        )
        return redirect('job_detail', job_id=job_id)
    
    messages.success(
        request,
        f'¡Inicio de obra confirmado! Se liberaron ${release_transaction.amount_usdc} USDC (30%) a {winning_bid.professional.nombre_completo}. '
        f'Se bloquearon ${remaining_transaction.amount_usdc} USDC (70% restante) hasta la finalización de la obra.'
    )
    
    return redirect('job_detail', job_id=job_id)


@login_required
def complete_work(request, job_id):
    """
    Vista para que el cliente confirme la finalización de obra.
    Libera el 70% restante menos la comisión del 5% al profesional.
    """
    if request.method != 'POST':
        return redirect('job_detail', job_id=job_id)
    
    job = get_object_or_404(JobOffer, id=job_id)
    
    # Verificar que el usuario sea el dueño
    if not hasattr(request.user, 'profile') or job.creator != request.user.profile:
        messages.error(request, 'No tienes permiso para finalizar la obra.')
        return redirect('job_detail', job_id=job_id)
    
    # Verificar que el trabajo esté en progreso
    if job.status != 'IN_PROGRESS':
        messages.error(request, 'El trabajo no está en progreso.')
        return redirect('job_detail', job_id=job_id)
    
    winning_bid = job.get_winning_bid()
    if not winning_bid:
        messages.error(request, 'No hay propuesta ganadora.')
        return redirect('job_detail', job_id=job_id)
    
    # Verificar si ya se finalizó
    already_completed = EscrowTransaction.objects.filter(
        job=job,
        transaction_type='FINAL_RELEASE',
        status='RELEASED'
    ).exists()
    
    if already_completed:
        messages.info(request, 'La obra ya fue finalizada anteriormente.')
        return redirect('job_detail', job_id=job_id)
    
    # Liberar pago final con comisión del 5%
    release_tx, fee_tx, success, error_msg = EscrowTransaction.release_final_payment(
        job=job,
        bid=winning_bid
    )
    
    if not success:
        messages.error(request, f'Error al liberar el pago final: {error_msg}')
        return redirect('job_detail', job_id=job_id)
    
    # Actualizar estado del trabajo
    job.status = 'CLOSED'
    job.save()
    
    messages.success(
        request,
        f'¡Obra finalizada! Se liberaron ${release_tx.amount_usdc} USDC (65% del total) a {winning_bid.professional.nombre_completo}. '
        f'Comisión de plataforma: ${fee_tx.amount_usdc} USDC (5%). ¡Gracias por usar nuestra plataforma!'
    )
    
    return redirect('job_detail', job_id=job_id)
