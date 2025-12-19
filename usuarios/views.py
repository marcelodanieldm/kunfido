from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Min, Avg
from .models import UserProfile, JobOffer, Proposal


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
    
    return render(request, 'usuarios/dashboard_home.html')


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
def votar_propuesta(request, propuesta_id):
    """
    Vista para que el dueño de la oferta vote/desvote una propuesta.
    """
    if request.method != 'POST':
        messages.error(request, 'Método no permitido.')
        return redirect('usuarios:ofertas_lista')
    
    propuesta = get_object_or_404(Proposal, id=propuesta_id)
    
    # Verificar que el usuario sea el creador de la oferta
    if request.user != propuesta.oferta.creador:
        messages.error(request, 'No tienes permiso para votar esta propuesta.')
        return redirect('usuarios:public_feed')
    
    # Toggle del voto
    propuesta.voto_owner = not propuesta.voto_owner
    propuesta.save()
    
    if propuesta.voto_owner:
        messages.success(request, f'Has votado la propuesta de {propuesta.profesional.get_full_name() or propuesta.profesional.username}')
    else:
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
