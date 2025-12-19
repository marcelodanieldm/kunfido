from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count, Min, Avg, Sum, Q
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.db import transaction
from decimal import Decimal
from .models import (
    UserProfile, JobOffer, Proposal, DelayJustification,
    Wallet, Transaction, WorkEvent
)
from django.contrib.auth.models import User
import csv
from datetime import timedelta


def home(request):
    """
    Vista principal de la aplicación.
    """
    return render(request, 'usuarios/home.html')


@login_required
def dashboard(request):
    """
    Dashboard principal del usuario con métricas según su rol.
    """
    # Verificar si el usuario tiene perfil
    if not hasattr(request.user, 'profile'):
        UserProfile.objects.create(user=request.user)
    
    # Si no ha seleccionado un rol, redirigir al onboarding
    if not request.user.profile.tipo_rol:
        messages.info(request, 'Por favor, completa tu perfil seleccionando un tipo de rol.')
        return redirect('usuarios:onboarding_rol')
    
    context = {}
    
    # Obtener o crear wallet del usuario
    wallet, created = Wallet.objects.get_or_create(
        user=request.user,
        defaults={
            'tipo_cuenta': 'USER',
            'balance_usdc': Decimal('1000.00')
        }
    )
    context['wallet'] = wallet
    
    # Obtener últimas transacciones del usuario
    transacciones_enviadas = Transaction.objects.filter(
        from_wallet=wallet
    ).select_related('to_wallet', 'oferta_relacionada', 'propuesta_relacionada')[:5]
    
    transacciones_recibidas = Transaction.objects.filter(
        to_wallet=wallet
    ).select_related('from_wallet', 'oferta_relacionada', 'propuesta_relacionada')[:5]
    
    # Combinar y ordenar por fecha
    from itertools import chain
    todas_transacciones = sorted(
        chain(transacciones_enviadas, transacciones_recibidas),
        key=lambda x: x.fecha_creacion,
        reverse=True
    )[:10]
    
    context['transacciones'] = todas_transacciones
    
    # Dashboard para OFICIO: incluir compromisos con atrasos
    if request.user.profile.tipo_rol == 'OFICIO':
        # Obtener trabajos en progreso del profesional
        # Asumiendo que existe una relación entre Proposal y JobOffer
        # Buscamos ofertas EN_PROGRESO donde el profesional tiene propuesta aceptada (voto_owner=True)
        mis_trabajos = JobOffer.objects.filter(
            status='EN_PROGRESO',
            propuestas__profesional=request.user,
            propuestas__voto_owner=True
        ).distinct().select_related('creador')
        
        # Identificar trabajos con atraso
        trabajos_atrasados = []
        trabajos_al_dia = []
        
        for trabajo in mis_trabajos:
            if trabajo.dias_atraso and trabajo.dias_atraso > 0:
                # Verificar si ya tiene justificación
                try:
                    justificacion = DelayJustification.objects.get(
                        oferta=trabajo,
                        profesional=request.user
                    )
                    trabajo.justificacion_existente = justificacion
                except DelayJustification.DoesNotExist:
                    trabajo.justificacion_existente = None
                
                trabajos_atrasados.append(trabajo)
            else:
                trabajos_al_dia.append(trabajo)
        
        context['trabajos_atrasados'] = trabajos_atrasados
        context['trabajos_al_dia'] = trabajos_al_dia
        context['total_compromisos'] = mis_trabajos.count()
    
    # Dashboard para CLIENTE (PERSONA o CONSORCIO): incluir réplicas pendientes
    elif request.user.profile.tipo_rol in ['PERSONA', 'CONSORCIO']:
        # Obtener ofertas del cliente con justificaciones pendientes
        replicas_pendientes = DelayJustification.objects.filter(
            oferta__creador=request.user,
            penalizacion_omitida=False  # Solo las que no han sido aceptadas
        ).select_related('oferta', 'profesional', 'profesional__profile').order_by('-fecha_creacion')
        
        context['replicas_pendientes'] = replicas_pendientes
        context['cantidad_replicas_pendientes'] = replicas_pendientes.count()
    
    return render(request, 'usuarios/dashboard_home.html', context)


@login_required
def onboarding_rol(request):
    """
    Vista para seleccionar o cambiar el tipo de rol del usuario.
    """
    # Verificar si el usuario tiene perfil
    if not hasattr(request.user, 'profile'):
        UserProfile.objects.create(user=request.user)
    
    if request.method == 'POST':
        tipo_rol = request.POST.get('tipo_rol')
        zona = request.POST.get('zona', '')
        
        if tipo_rol in ['PERSONA', 'CONSORCIO', 'OFICIO']:
            profile = request.user.profile
            profile.tipo_rol = tipo_rol
            if zona:
                profile.zona = zona
            profile.save()
            
            messages.success(request, f'¡Perfil actualizado! Ahora eres un {profile.get_tipo_rol_display()}.')
            return redirect('usuarios:dashboard')
        else:
            messages.error(request, 'Por favor, selecciona un tipo de rol válido.')
    
    return render(request, 'usuarios/onboarding_rol.html')


def public_feed(request):
    """
    Feed público de ofertas accesible sin autenticación.
    """
    # Obtener ofertas abiertas con anotaciones
    ofertas = JobOffer.objects.filter(status='ABIERTA').annotate(
        num_propuestas=Count('propuestas'),
        monto_minimo=Min('propuestas__monto')
    ).select_related('creador', 'creador__profile').order_by('-fecha_creacion')
    
    # Calcular estadísticas generales
    total_propuestas = Proposal.objects.filter(oferta__status='ABIERTA').count()
    promedio_presupuesto = ofertas.aggregate(Avg('presupuesto_ars'))['presupuesto_ars__avg'] or 0
    
    context = {
        'ofertas': ofertas,
        'total_propuestas': total_propuestas,
        'promedio_presupuesto': promedio_presupuesto,
    }
    return render(request, 'usuarios/public_feed.html', context)


def ofertas_lista(request):
    """
    Vista pública que lista todas las ofertas de trabajo abiertas.
    Muestra información de propuestas para usuarios autenticados.
    """
    # Obtener ofertas abiertas con anotaciones
    ofertas = JobOffer.objects.filter(status='ABIERTA').annotate(
        num_propuestas=Count('propuestas'),
        monto_minimo=Min('propuestas__monto')
    ).select_related('creador').order_by('-fecha_creacion')
    
    # Si el usuario está autenticado y es OFICIO, incluir sus propuestas
    mis_propuestas = {}
    if request.user.is_authenticated and hasattr(request.user, 'profile'):
        if request.user.profile.tipo_rol == 'OFICIO':
            propuestas_usuario = Proposal.objects.filter(
                profesional=request.user,
                oferta__status='ABIERTA'
            ).select_related('oferta')
            mis_propuestas = {p.oferta_id: p for p in propuestas_usuario}
    
    context = {
        'ofertas': ofertas,
        'mis_propuestas': mis_propuestas,
    }
    return render(request, 'usuarios/ofertas_lista.html', context)


def job_detail_public(request, oferta_id):
    """
    Vista pública del detalle de una oferta.
    Accesible sin autenticación, muestra botón "Ingresa para ofertar".
    """
    oferta = get_object_or_404(JobOffer, id=oferta_id)
    
    # Contar propuestas y obtener monto mínimo
    num_propuestas = oferta.propuestas.count()
    monto_minimo = oferta.propuestas.aggregate(Min('monto'))['monto__min']
    
    context = {
        'oferta': oferta,
        'num_propuestas': num_propuestas,
        'monto_minimo': monto_minimo,
    }
    return render(request, 'usuarios/job_detail_public.html', context)


@login_required
def job_detail_private(request, oferta_id):
    """
    Vista privada para el dueño de la oferta.
    Muestra tabla comparativa de todas las propuestas con botón de votación.
    """
    oferta = get_object_or_404(JobOffer, id=oferta_id, creador=request.user)
    
    # Obtener propuestas ordenadas por monto
    propuestas = oferta.propuestas.select_related(
        'profesional', 
        'profesional__profile'
    ).order_by('monto')
    
    # Calcular estadísticas
    monto_minimo = propuestas.aggregate(Min('monto'))['monto__min']
    promedio_monto = propuestas.aggregate(Avg('monto'))['monto__avg']
    dias_promedio = propuestas.aggregate(Avg('dias_entrega'))['dias_entrega__avg']
    
    context = {
        'oferta': oferta,
        'propuestas': propuestas,
        'monto_minimo': monto_minimo,
        'promedio_monto': promedio_monto,
        'dias_promedio': dias_promedio,
    }
    return render(request, 'usuarios/job_detail_private.html', context)


@login_required
def oferta_detalle(request, oferta_id):
    """
    Vista detallada de una oferta con todas las propuestas (si es el creador).
    """
    oferta = get_object_or_404(JobOffer, id=oferta_id)
    
    # Verificar si el usuario es el creador de la oferta
    es_creador = request.user == oferta.creador
    
    # Obtener propuestas
    propuestas = oferta.propuestas.select_related('profesional', 'profesional__profile').order_by('monto')
    
    # Verificar si el usuario ya tiene una propuesta
    mi_propuesta = None
    if hasattr(request.user, 'profile') and request.user.profile.tipo_rol == 'OFICIO':
        try:
            mi_propuesta = Proposal.objects.get(oferta=oferta, profesional=request.user)
        except Proposal.DoesNotExist:
            pass
    
    context = {
        'oferta': oferta,
        'propuestas': propuestas if es_creador else None,
        'mi_propuesta': mi_propuesta,
        'es_creador': es_creador,
    }
    return render(request, 'usuarios/oferta_detalle.html', context)


@login_required
@require_POST
def votar_propuesta(request, propuesta_id):
    """
    Vista para que el dueño de la oferta vote/desvote una propuesta.
    Cuando se acepta (vota) una propuesta, se inicia el proceso de transacción:
    1. Verifica saldo en USDC_MOCK
    2. Retiene 30% en Plataforma_Escrow
    3. Emite evento 'Trabajo Iniciado'
    """
    propuesta = get_object_or_404(Proposal, id=propuesta_id)
    
    # Verificar que el usuario sea el creador de la oferta
    if request.user != propuesta.oferta.creador:
        messages.error(request, 'No tienes permiso para votar esta propuesta.')
        return redirect('usuarios:public_feed')
    
    # Determinar si se está votando o desvotando
    esta_votando = not propuesta.voto_owner
    
    if esta_votando:
        # **PROCESO DE ACEPTACIÓN CON TRANSACCIÓN**
        
        # 1. Verificar/crear wallet del cliente
        cliente_wallet, created = Wallet.objects.get_or_create(
            user=request.user,
            defaults={
                'tipo_cuenta': 'USER',
                'balance_usdc': Decimal('1000.00')  # Saldo inicial demo
            }
        )
        
        # 2. Verificar saldo suficiente (30% del monto de la propuesta)
        monto_propuesta = Decimal(str(propuesta.monto))
        porcentaje_escrow = Decimal('30')
        monto_requerido = (monto_propuesta * porcentaje_escrow / Decimal('100')).quantize(
            Decimal('0.01')
        )
        
        if not cliente_wallet.tiene_saldo_suficiente(monto_requerido):
            messages.error(
                request,
                f'Saldo insuficiente. Necesitas {monto_requerido} USDC_MOCK para aceptar esta propuesta. '
                f'Tu saldo actual: {cliente_wallet.balance_usdc} USDC_MOCK'
            )
            return redirect('usuarios:job_detail_private', oferta_id=propuesta.oferta.id)
        
        # 3. Procesar transacción en contexto atómico
        try:
            with transaction.atomic():
                # Crear transacción de escrow
                transaccion, monto_escrow = Transaction.crear_transaccion_escrow(
                    cliente_wallet=cliente_wallet,
                    monto_total=propuesta.monto,
                    propuesta=propuesta,
                    porcentaje_escrow=30
                )
                
                if not transaccion:
                    raise Exception('Error al procesar la transacción de escrow')
                
                # Marcar propuesta como votada
                propuesta.voto_owner = True
                propuesta.save()
                
                # Cambiar estado de la oferta a EN_PROGRESO
                propuesta.oferta.status = 'EN_PROGRESO'
                propuesta.oferta.fecha_inicio = timezone.now()
                # Calcular fecha de entrega pactada
                from datetime import timedelta
                propuesta.oferta.fecha_entrega_pactada = timezone.now() + timedelta(days=propuesta.dias_entrega)
                propuesta.oferta.save()
                
                # 4. Emitir evento de 'Trabajo Iniciado'
                evento = WorkEvent.crear_evento_trabajo_iniciado(
                    oferta=propuesta.oferta,
                    propuesta=propuesta,
                    transaccion=transaccion
                )
                
                # Mensaje de éxito detallado
                messages.success(
                    request,
                    f'✓ Propuesta aceptada exitosamente! '
                    f'Se han retenido {monto_escrow} USDC_MOCK en garantía (30%). '
                    f'El trabajo ha sido iniciado con {propuesta.profesional.get_full_name() or propuesta.profesional.username}.'
                )
                
                # Información adicional
                messages.info(
                    request,
                    f'💰 Saldo actual: {cliente_wallet.balance_usdc} USDC_MOCK | '
                    f'📅 Fecha de entrega: {propuesta.oferta.fecha_entrega_pactada.strftime("%d/%m/%Y")}'
                )
        
        except Exception as e:
            messages.error(
                request,
                f'Error al procesar la transacción: {str(e)}. Por favor, intenta nuevamente.'
            )
            return redirect('usuarios:job_detail_private', oferta_id=propuesta.oferta.id)
    
    else:
        # **PROCESO DE DESVOTACIÓN**
        propuesta.voto_owner = False
        propuesta.save()
        messages.info(request, 'Voto removido.')
    
    return redirect('usuarios:job_detail_private', oferta_id=propuesta.oferta.id)


@login_required
def crear_propuesta(request, oferta_id):
    """
    Vista para crear o actualizar una propuesta (contraoferta).
    Solo usuarios con rol OFICIO pueden crear propuestas.
    """
    # Verificar que el usuario tenga perfil y sea OFICIO
    if not hasattr(request.user, 'profile'):
        messages.error(request, 'Debes completar tu perfil primero.')
        return redirect('usuarios:onboarding_rol')
    
    if request.user.profile.tipo_rol != 'OFICIO':
        messages.error(request, 'Solo los profesionales pueden crear propuestas.')
        return redirect('usuarios:public_feed')
    
    oferta = get_object_or_404(JobOffer, id=oferta_id, status='ABIERTA')
    
    # Verificar si el usuario ya tiene una propuesta (contraoferta)
    try:
        propuesta = Proposal.objects.get(oferta=oferta, profesional=request.user)
        es_actualizacion = True
    except Proposal.DoesNotExist:
        propuesta = None
        es_actualizacion = False
    
    if request.method == 'POST':
        monto = request.POST.get('monto')
        dias_entrega = request.POST.get('dias_entrega')
        comentario = request.POST.get('comentario', '')
        
        try:
            monto = float(monto)
            dias_entrega = int(dias_entrega)
            
            if monto <= 0 or dias_entrega <= 0:
                messages.error(request, 'El monto y los días deben ser valores positivos.')
            else:
                if es_actualizacion:
                    # Actualizar propuesta existente (contraoferta/puja)
                    propuesta.monto = monto
                    propuesta.dias_entrega = dias_entrega
                    propuesta.comentario = comentario
                    propuesta.save()
                    messages.success(request, f'¡Contraoferta enviada! (Versión {propuesta.version})')
                else:
                    # Crear nueva propuesta
                    propuesta = Proposal.objects.create(
                        oferta=oferta,
                        profesional=request.user,
                        monto=monto,
                        dias_entrega=dias_entrega,
                        comentario=comentario
                    )
                    messages.success(request, '¡Propuesta enviada exitosamente!')
                
                return redirect('usuarios:job_detail_public', oferta_id=oferta.id)
        
        except (ValueError, TypeError):
            messages.error(request, 'Por favor, ingresa valores válidos.')
    
    context = {
        'oferta': oferta,
        'propuesta': propuesta,
        'es_actualizacion': es_actualizacion,
    }
    return render(request, 'usuarios/crear_propuesta.html', context)


@login_required
def crear_justificacion_atraso(request, oferta_id):
    """
    Vista para que el profesional (OFICIO) cree una justificación de atraso.
    Solo puede haber una justificación por oferta y profesional.
    """
    # Verificar que el usuario sea OFICIO
    if not hasattr(request.user, 'profile') or request.user.profile.tipo_rol != 'OFICIO':
        messages.error(request, 'Solo los profesionales pueden justificar atrasos.')
        return redirect('usuarios:public_feed')
    
    oferta = get_object_or_404(JobOffer, id=oferta_id)
    
    # Calcular días de atraso
    dias_atraso = oferta.dias_atraso
    if dias_atraso is None or dias_atraso == 0:
        messages.error(request, 'Esta oferta no tiene atrasos que justificar.')
        return redirect('usuarios:job_detail_public', oferta_id=oferta.id)
    
    # Verificar si ya existe una justificación
    try:
        justificacion = DelayJustification.objects.get(oferta=oferta, profesional=request.user)
        es_actualizacion = True
    except DelayJustification.DoesNotExist:
        justificacion = None
        es_actualizacion = False
    
    if request.method == 'POST':
        replica = request.POST.get('replica', '').strip()
        
        if not replica:
            messages.error(request, 'Debes escribir una justificación.')
        else:
            if es_actualizacion:
                # Actualizar justificación existente
                justificacion.replica = replica
                justificacion.dias_atraso_justificados = dias_atraso
                justificacion.save()
                messages.success(request, 'Justificación actualizada exitosamente.')
            else:
                # Crear nueva justificación
                justificacion = DelayJustification.objects.create(
                    oferta=oferta,
                    profesional=request.user,
                    replica=replica,
                    dias_atraso_justificados=dias_atraso
                )
                messages.success(request, 'Justificación enviada exitosamente.')
            
            return redirect('usuarios:job_detail_public', oferta_id=oferta.id)
    
    context = {
        'oferta': oferta,
        'justificacion': justificacion,
        'es_actualizacion': es_actualizacion,
        'dias_atraso': dias_atraso,
    }
    return render(request, 'usuarios/crear_justificacion_atraso.html', context)


@login_required
@require_POST
def aceptar_replica_atraso(request, justificacion_id):
    """
    Endpoint para que el cliente (dueño de la oferta) acepte la réplica del profesional.
    Setea el flag penalizacion_omitida=True.
    """
    justificacion = get_object_or_404(DelayJustification, id=justificacion_id)
    
    # Verificar que el usuario sea el dueño de la oferta
    if request.user != justificacion.oferta.creador:
        messages.error(request, 'No tienes permiso para aceptar esta justificación.')
        return redirect('usuarios:public_feed')
    
    # Verificar que no haya sido aceptada previamente
    if justificacion.penalizacion_omitida:
        messages.info(request, 'Esta justificación ya fue aceptada anteriormente.')
    else:
        # Aceptar la justificación
        justificacion.aceptar_justificacion(aceptado_por=request.user)
        messages.success(
            request, 
            f'Has aceptado la justificación de {justificacion.profesional.get_full_name() or justificacion.profesional.username}. '
            f'La penalización por {justificacion.dias_atraso_justificados} días de atraso ha sido omitida.'
        )
    
    return redirect('usuarios:job_detail_private', oferta_id=justificacion.oferta.id)


@login_required
@require_POST
def rechazar_replica_atraso(request, justificacion_id):
    """
    Endpoint para que el cliente rechace la réplica (opcional).
    La penalización se mantiene activa.
    """
    justificacion = get_object_or_404(DelayJustification, id=justificacion_id)
    
    # Verificar que el usuario sea el dueño de la oferta
    if request.user != justificacion.oferta.creador:
        messages.error(request, 'No tienes permiso para rechazar esta justificación.')
        return redirect('usuarios:public_feed')
    
    messages.info(
        request,
        f'Has rechazado la justificación. La penalización por {justificacion.dias_atraso_justificados} días de atraso se mantiene.'
    )
    
    return redirect('usuarios:job_detail_private', oferta_id=justificacion.oferta.id)


@login_required
@require_POST
def aprobar_trabajo_completado(request, oferta_id):
    """
    Vista para que el cliente apruebe un trabajo completado.
    Libera fondos del escrow al profesional y cobra comisión de plataforma.
    """
    oferta = get_object_or_404(JobOffer, id=oferta_id)
    
    # Verificar que el usuario sea el dueño de la oferta
    if request.user != oferta.creador:
        messages.error(request, 'No tienes permiso para aprobar este trabajo.')
        return redirect('usuarios:public_feed')
    
    # Verificar que el trabajo esté en progreso
    if oferta.status != 'EN_PROGRESO':
        messages.error(request, 'Este trabajo no está en progreso.')
        return redirect('usuarios:job_detail_private', oferta_id=oferta.id)
    
    # Obtener la propuesta aceptada (votada)
    propuesta = oferta.propuestas.filter(voto_owner=True).first()
    if not propuesta:
        messages.error(request, 'No se encontró la propuesta aceptada.')
        return redirect('usuarios:job_detail_private', oferta_id=oferta.id)
    
    # Procesar liberación de pago con transacción atómica
    try:
        with transaction.atomic():
            # Liberar pago al profesional (con comisión del 10%)
            transaccion_pago, transaccion_comision, monto_liberado = Transaction.liberar_pago_a_profesional(
                propuesta=propuesta,
                porcentaje_comision=10
            )
            
            if not transaccion_pago:
                raise Exception('Error al procesar la liberación de fondos')
            
            # Actualizar estado de la oferta
            oferta.status = 'COMPLETADO'
            oferta.fecha_entrega_real = timezone.now()
            oferta.save()
            
            # Crear evento de trabajo completado
            WorkEvent.crear_evento_trabajo_completado(
                oferta=oferta,
                propuesta=propuesta,
                transaccion_pago=transaccion_pago,
                transaccion_comision=transaccion_comision
            )
            
            # Mensajes de éxito
            messages.success(
                request,
                f'✓ Trabajo aprobado exitosamente! '
                f'Se han liberado {monto_liberado} USDC_MOCK a {propuesta.profesional.get_full_name() or propuesta.profesional.username}.'
            )
            messages.info(
                request,
                f'📊 Desglose: Pago al profesional: {monto_liberado} USDC | '
                f'Comisión de plataforma (10%): {transaccion_comision.monto_usdc} USDC'
            )
    
    except Exception as e:
        messages.error(
            request,
            f'Error al aprobar el trabajo: {str(e)}. Por favor, intenta nuevamente.'
        )
    
    return redirect('usuarios:job_detail_private', oferta_id=oferta.id)


@login_required
@require_POST
def rechazar_trabajo_completado(request, oferta_id):
    """
    Vista para que el cliente rechace un trabajo completado.
    Esto inicia un proceso de disputa/revisión.
    """
    oferta = get_object_or_404(JobOffer, id=oferta_id)
    
    # Verificar que el usuario sea el dueño de la oferta
    if request.user != oferta.creador:
        messages.error(request, 'No tienes permiso para rechazar este trabajo.')
        return redirect('usuarios:public_feed')
    
    # Verificar que el trabajo esté en progreso
    if oferta.status != 'EN_PROGRESO':
        messages.error(request, 'Este trabajo no está en progreso.')
        return redirect('usuarios:job_detail_private', oferta_id=oferta.id)
    
    motivo = request.POST.get('motivo', 'Cliente no satisfecho con la entrega')
    
    # Cambiar estado a disputa
    oferta.status = 'ABIERTO'  # Vuelve a estado abierto para revisión
    oferta.save()
    
    messages.warning(
        request,
        f'Has rechazado el trabajo. El estado ha vuelto a "Abierto" para revisión. '
        f'Motivo: {motivo}'
    )
    
    return redirect('usuarios:job_detail_private', oferta_id=oferta.id)


@login_required
@require_POST
def solicitar_reembolso(request, oferta_id):
    """
    Vista para que el cliente solicite un reembolso.
    Devuelve el dinero de escrow al cliente.
    """
    oferta = get_object_or_404(JobOffer, id=oferta_id)
    
    # Verificar que el usuario sea el dueño de la oferta
    if request.user != oferta.creador:
        messages.error(request, 'No tienes permiso para solicitar reembolso de este trabajo.')
        return redirect('usuarios:public_feed')
    
    # Verificar que el trabajo esté en progreso o abierto
    if oferta.status not in ['EN_PROGRESO', 'ABIERTO']:
        messages.error(request, 'No se puede solicitar reembolso para este trabajo.')
        return redirect('usuarios:job_detail_private', oferta_id=oferta.id)
    
    # Obtener la propuesta aceptada
    propuesta = oferta.propuestas.filter(voto_owner=True).first()
    if not propuesta:
        messages.error(request, 'No se encontró la propuesta aceptada.')
        return redirect('usuarios:job_detail_private', oferta_id=oferta.id)
    
    motivo = request.POST.get('motivo', 'Solicitud de reembolso por el cliente')
    
    # Procesar reembolso con transacción atómica
    try:
        with transaction.atomic():
            # Procesar reembolso
            transaccion_reembolso, monto_reembolsado = Transaction.procesar_reembolso(
                propuesta=propuesta,
                motivo=motivo
            )
            
            if not transaccion_reembolso:
                raise Exception('Error al procesar el reembolso. Verifica que haya fondos en escrow.')
            
            # Actualizar estado de la oferta
            oferta.status = 'CANCELADO'
            oferta.save()
            
            # Crear evento de reembolso
            WorkEvent.crear_evento_reembolso(
                oferta=oferta,
                propuesta=propuesta,
                transaccion_reembolso=transaccion_reembolso,
                motivo=motivo
            )
            
            # Mensajes de éxito
            messages.success(
                request,
                f'✓ Reembolso procesado exitosamente! '
                f'Se han devuelto {monto_reembolsado} USDC_MOCK a tu billetera.'
            )
            messages.info(request, f'Motivo: {motivo}')
    
    except Exception as e:
        messages.error(
            request,
            f'Error al procesar el reembolso: {str(e)}. Por favor, intenta nuevamente.'
        )
    
    return redirect('usuarios:job_detail_private', oferta_id=oferta.id)


@login_required
def wallet_detalle(request):
    """
    Vista detallada de la billetera del usuario.
    Muestra saldo, historial de transacciones y opciones de carga.
    """
    # Obtener o crear wallet del usuario
    wallet, created = Wallet.objects.get_or_create(
        user=request.user,
        defaults={
            'tipo_cuenta': 'USER',
            'balance_usdc': Decimal('1000.00')
        }
    )
    
    # Obtener todas las transacciones del usuario
    transacciones_enviadas = Transaction.objects.filter(
        from_wallet=wallet
    ).select_related('to_wallet', 'oferta_relacionada', 'propuesta_relacionada')
    
    transacciones_recibidas = Transaction.objects.filter(
        to_wallet=wallet
    ).select_related('from_wallet', 'oferta_relacionada', 'propuesta_relacionada')
    
    # Combinar y ordenar por fecha
    from itertools import chain
    todas_transacciones = sorted(
        chain(transacciones_enviadas, transacciones_recibidas),
        key=lambda x: x.fecha_creacion,
        reverse=True
    )
    
    # Calcular estadísticas
    total_enviado = sum(
        t.monto_usdc for t in transacciones_enviadas 
        if t.status == 'COMPLETED'
    )
    total_recibido = sum(
        t.monto_usdc for t in transacciones_recibidas 
        if t.status == 'COMPLETED'
    )
    
    context = {
        'wallet': wallet,
        'transacciones': todas_transacciones,
        'total_enviado': total_enviado,
        'total_recibido': total_recibido,
        'tasa_conversion': Decimal('1250.00'),  # ARS por USDC (simulado)
    }
    
    return render(request, 'usuarios/wallet.html', context)


@login_required
@require_POST
def cargar_fondos(request):
    """
    Simula la carga de fondos convirtiendo ARS a USDC_MOCK.
    """
    try:
        monto_ars = Decimal(request.POST.get('monto_ars', '0'))
        
        if monto_ars <= 0:
            messages.error(request, 'El monto debe ser mayor a cero.')
            return redirect('usuarios:wallet_detalle')
        
        # Tasa de conversión simulada (1 USDC = 1250 ARS)
        tasa_conversion = Decimal('1250.00')
        monto_usdc = (monto_ars / tasa_conversion).quantize(
            Decimal('0.01'),
            rounding='ROUND_HALF_UP'
        )
        
        # Obtener o crear wallet
        wallet, created = Wallet.objects.get_or_create(
            user=request.user,
            defaults={
                'tipo_cuenta': 'USER',
                'balance_usdc': Decimal('0.00')
            }
        )
        
        # Obtener cuenta del sistema (escrow) como origen
        sistema_wallet = Wallet.get_escrow_account()
        
        with transaction.atomic():
            # Crear transacción de carga
            trans = Transaction.objects.create(
                from_wallet=sistema_wallet,
                to_wallet=wallet,
                monto_usdc=monto_usdc,
                tipo_transaccion='REFUND',  # Usamos REFUND para cargas manuales
                status='PENDING',
                descripcion=f'Carga de fondos: ${monto_ars} ARS → {monto_usdc} USDC (Tasa: ${tasa_conversion})',
                metadata={
                    'monto_ars': str(monto_ars),
                    'tasa_conversion': str(tasa_conversion),
                    'tipo': 'carga_manual'
                }
            )
            
            # Sumar al balance del usuario
            wallet.sumar_saldo(monto_usdc)
            
            # Marcar como completada
            trans.status = 'COMPLETED'
            trans.save()
            
            messages.success(
                request,
                f'✓ Fondos cargados exitosamente! '
                f'${monto_ars} ARS = {monto_usdc} USDC_MOCK. '
                f'Nuevo balance: {wallet.balance_usdc} USDC'
            )
    
    except ValueError:
        messages.error(request, 'Monto inválido. Por favor, ingresa un número válido.')
    except Exception as e:
        messages.error(request, f'Error al cargar fondos: {str(e)}')
    
    return redirect('usuarios:wallet_detalle')


@user_passes_test(lambda u: u.is_superuser)
def admin_custom_dashboard(request):
    """
    Dashboard administrativo personalizado con KPIs del sistema.
    Solo accesible para superusuarios.
    """
    # KPI 1: Volumen Total Transaccionado (GMV)
    gmv_data = Transaction.objects.filter(
        status='COMPLETED'
    ).aggregate(
        total=Sum('monto_usdc')
    )
    gmv = gmv_data['total'] or Decimal('0.00')
    
    # KPI 2: Comisión Acumulada
    comision_data = Transaction.objects.filter(
        tipo_transaccion='FEE',
        status='COMPLETED'
    ).aggregate(
        total=Sum('monto_usdc')
    )
    comision_acumulada = comision_data['total'] or Decimal('0.00')
    
    # KPI 3: Tasa de Atrasos Promedio
    # Obtener trabajos finalizados con fecha límite y fecha de finalización
    trabajos_finalizados = JobOffer.objects.filter(
        status__in=['FINALIZADA', 'EN_PROGRESO']
    ).exclude(
        fecha_limite__isnull=True
    )
    
    total_trabajos = trabajos_finalizados.count()
    trabajos_atrasados = 0
    dias_atraso_total = 0
    
    for trabajo in trabajos_finalizados:
        # Buscar evento de trabajo completado
        evento_completado = WorkEvent.objects.filter(
            oferta=trabajo,
            tipo_evento='TRABAJO_COMPLETADO'
        ).first()
        
        if evento_completado:
            fecha_completado = evento_completado.fecha_evento
            if fecha_completado > trabajo.fecha_limite:
                trabajos_atrasados += 1
                dias_atraso = (fecha_completado - trabajo.fecha_limite).days
                dias_atraso_total += dias_atraso
    
    tasa_atrasos = (trabajos_atrasados / total_trabajos * 100) if total_trabajos > 0 else 0
    promedio_dias_atraso = (dias_atraso_total / trabajos_atrasados) if trabajos_atrasados > 0 else 0
    
    # KPI 4: Usuarios Activos (últimos 30 días)
    fecha_limite_actividad = timezone.now() - timedelta(days=30)
    usuarios_activos = User.objects.filter(
        Q(ofertas_creadas__fecha_creacion__gte=fecha_limite_actividad) |
        Q(propuestas__fecha_creacion__gte=fecha_limite_actividad) |
        Q(transacciones_enviadas__fecha_creacion__gte=fecha_limite_actividad) |
        Q(transacciones_recibidas__fecha_creacion__gte=fecha_limite_actividad)
    ).distinct().count()
    
    # Estadísticas adicionales
    total_usuarios = User.objects.count()
    total_trabajos = JobOffer.objects.count()
    trabajos_completados = JobOffer.objects.filter(status='FINALIZADA').count()
    total_transacciones = Transaction.objects.filter(status='COMPLETED').count()
    
    context = {
        'gmv': gmv,
        'comision_acumulada': comision_acumulada,
        'tasa_atrasos': round(tasa_atrasos, 2),
        'promedio_dias_atraso': round(promedio_dias_atraso, 1),
        'usuarios_activos': usuarios_activos,
        'total_usuarios': total_usuarios,
        'total_trabajos': total_trabajos,
        'trabajos_completados': trabajos_completados,
        'total_transacciones': total_transacciones,
    }
    
    return render(request, 'admin/custom_dashboard.html', context)


@user_passes_test(lambda u: u.is_superuser)
def exportar_trabajos_csv(request):
    """
    Exporta un CSV con todos los trabajos terminados y sus montos.
    Solo accesible para superusuarios.
    """
    # Crear la respuesta HTTP con el tipo de contenido CSV
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = 'attachment; filename="trabajos_terminados.csv"'
    
    # Agregar BOM para compatibilidad con Excel
    response.write('\ufeff')
    
    # Crear el writer CSV
    writer = csv.writer(response)
    
    # Escribir encabezados
    writer.writerow([
        'ID Trabajo',
        'Título',
        'Cliente',
        'Email Cliente',
        'Profesional Asignado',
        'Email Profesional',
        'Monto Total (USDC)',
        'Fecha Creación',
        'Fecha Límite',
        'Fecha Finalización',
        'Estado',
        'Comisión Kunfido (USDC)',
        'Pago a Profesional (USDC)',
    ])
    
    # Obtener trabajos finalizados
    trabajos = JobOffer.objects.filter(
        status='FINALIZADA'
    ).select_related(
        'creador',
        'profesional_asignado'
    ).order_by('-fecha_creacion')
    
    # Escribir datos
    for trabajo in trabajos:
        # Buscar transacciones relacionadas
        trans_escrow = Transaction.objects.filter(
            oferta_relacionada=trabajo,
            tipo_transaccion='ESCROW',
            status='COMPLETED'
        ).first()
        
        trans_pago = Transaction.objects.filter(
            oferta_relacionada=trabajo,
            tipo_transaccion='PAYMENT',
            status='COMPLETED'
        ).first()
        
        trans_fee = Transaction.objects.filter(
            oferta_relacionada=trabajo,
            tipo_transaccion='FEE',
            status='COMPLETED'
        ).first()
        
        # Buscar fecha de finalización
        evento_completado = WorkEvent.objects.filter(
            oferta=trabajo,
            tipo_evento='TRABAJO_COMPLETADO'
        ).first()
        
        fecha_finalizacion = evento_completado.fecha_evento if evento_completado else trabajo.fecha_actualizacion
        
        monto_total = trans_escrow.monto_usdc if trans_escrow else Decimal('0.00')
        comision = trans_fee.monto_usdc if trans_fee else Decimal('0.00')
        pago_profesional = trans_pago.monto_usdc if trans_pago else Decimal('0.00')
        
        writer.writerow([
            trabajo.id,
            trabajo.titulo,
            trabajo.creador.get_full_name() or trabajo.creador.username,
            trabajo.creador.email,
            trabajo.profesional_asignado.get_full_name() if trabajo.profesional_asignado else 'N/A',
            trabajo.profesional_asignado.email if trabajo.profesional_asignado else 'N/A',
            str(monto_total),
            trabajo.fecha_creacion.strftime('%Y-%m-%d %H:%M'),
            trabajo.fecha_limite.strftime('%Y-%m-%d') if trabajo.fecha_limite else 'N/A',
            fecha_finalizacion.strftime('%Y-%m-%d %H:%M'),
            trabajo.get_status_display(),
            str(comision),
            str(pago_profesional),
        ])
    
    return response
