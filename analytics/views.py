import csv
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Sum, Q, Count, F
from django.utils import timezone
from django.contrib import messages
from jobs.models import JobOffer, Bid, EscrowTransaction
from usuarios.models import UserProfile, Wallet, Transaction


@user_passes_test(lambda u: u.is_superuser)
def superuser_dashboard(request):
    """
    Dashboard exclusivo para superusuarios con KPIs del negocio.
    
    KPIs Implementados:
    - GMV_Total: Gross Merchandise Value (suma de presupuestos de trabajos en progreso y finalizados)
    - Comisiones_Acumuladas: 5% de trabajos finalizados (ARS y USDC)
    - Fondos_en_Escrow: Dinero bloqueado en garantía
    - Tasa_de_Atraso: Porcentaje de trabajos con retrasos
    """
    
    # ========== KPI 1: GMV TOTAL ==========
    # Suma de todos los presupuestos de trabajos IN_PROGRESS y CLOSED (FINISHED)
    gmv_data = JobOffer.objects.filter(
        Q(status='IN_PROGRESS') | Q(status='CLOSED')
    ).aggregate(
        total_ars=Sum('budget_base_ars')
    )
    
    gmv_total_ars = gmv_data['total_ars'] or Decimal('0.00')
    
    # Para USDC: necesitamos sumar los montos de las pujas ganadoras
    gmv_usdc_data = Bid.objects.filter(
        is_winner=True,
        job_offer__status__in=['IN_PROGRESS', 'CLOSED']
    ).aggregate(
        total_usdc=Sum('amount_ars')  # Nota: si tienes amount_usdc, usar ese campo
    )
    
    # Simulación: dividir por tipo de cambio aproximado (ej: 1000 ARS = 1 USDC)
    gmv_total_usdc = (gmv_usdc_data['total_usdc'] or Decimal('0.00')) / Decimal('1000.00')
    
    
    # ========== KPI 2: COMISIONES ACUMULADAS ==========
    # 5% de todos los trabajos CLOSED (finalizados)
    comisiones_data = JobOffer.objects.filter(
        status='CLOSED'
    ).aggregate(
        total_finalizados_ars=Sum('budget_base_ars')
    )
    
    total_finalizados_ars = comisiones_data['total_finalizados_ars'] or Decimal('0.00')
    comision_tasa = Decimal('0.05')  # 5%
    comisiones_ars = (total_finalizados_ars * comision_tasa).quantize(
        Decimal('0.01'), 
        rounding=ROUND_HALF_UP
    )
    
    # Comisiones en USDC (desde EscrowTransaction con tipo PLATFORM_FEE)
    comisiones_usdc_data = EscrowTransaction.objects.filter(
        transaction_type='PLATFORM_FEE',
        status='RELEASED'
    ).aggregate(
        total_comision_usdc=Sum('amount_usdc')
    )
    
    comisiones_usdc = comisiones_usdc_data['total_comision_usdc'] or Decimal('0.00')
    
    
    # ========== KPI 3: FONDOS EN ESCROW ==========
    # Suma de todas las transacciones LOCKED (bloqueadas) actualmente
    fondos_escrow_data = EscrowTransaction.objects.filter(
        status='LOCKED'
    ).aggregate(
        total_bloqueado=Sum('amount_usdc')
    )
    
    fondos_en_escrow = fondos_escrow_data['total_bloqueado'] or Decimal('0.00')
    
    
    # ========== KPI 4: TASA DE ATRASO ==========
    # Porcentaje de trabajos IN_PROGRESS con is_delayed=True
    trabajos_en_progreso = JobOffer.objects.filter(status='IN_PROGRESS').count()
    trabajos_atrasados = JobOffer.objects.filter(
        status='IN_PROGRESS',
        is_delayed=True
    ).count()
    
    if trabajos_en_progreso > 0:
        tasa_atraso = (trabajos_atrasados / trabajos_en_progreso) * 100
    else:
        tasa_atraso = 0.0
    
    
    # ========== MÉTRICAS ADICIONALES ==========
    # Total de usuarios por tipo de rol
    usuarios_stats = UserProfile.objects.values('tipo_rol').annotate(
        total=Count('id')
    )
    
    # Total de trabajos por estado
    trabajos_stats = JobOffer.objects.values('status').annotate(
        total=Count('id')
    )
    
    # Total de transacciones escrow por tipo
    escrow_stats = EscrowTransaction.objects.values('transaction_type').annotate(
        total=Count('id'),
        monto_total=Sum('amount_usdc')
    )
    
    # Últimas 10 transacciones de escrow
    ultimas_transacciones = EscrowTransaction.objects.select_related(
        'job', 'bid', 'from_wallet', 'to_wallet'
    ).order_by('-created_at')[:10]
    
    
    context = {
        # KPIs Principales
        'gmv_total_ars': gmv_total_ars,
        'gmv_total_usdc': gmv_total_usdc,
        'comisiones_ars': comisiones_ars,
        'comisiones_usdc': comisiones_usdc,
        'fondos_en_escrow': fondos_en_escrow,
        'tasa_atraso': round(tasa_atraso, 2),
        'trabajos_en_progreso': trabajos_en_progreso,
        'trabajos_atrasados': trabajos_atrasados,
        
        # Stats adicionales
        'usuarios_stats': usuarios_stats,
        'trabajos_stats': trabajos_stats,
        'escrow_stats': escrow_stats,
        'ultimas_transacciones': ultimas_transacciones,
        
        # Fecha del reporte
        'fecha_reporte': timezone.now(),
    }
    
    return render(request, 'analytics/superuser_dashboard.html', context)


@user_passes_test(lambda u: u.is_superuser)
def admin_dashboard(request):
    """
    Dashboard administrativo avanzado con Bootstrap 5.
    
    Incluye:
    - 4 indicadores principales (cards)
    - Gráfico de crecimiento (Chart.js)
    - Lista de alerta (trabajos atrasados)
    - Admin de usuarios (buscador)
    - Botón de exportación
    """
    
    # ========== INDICADORES (CARDS) ==========
    
    # 1. Ingresos Totales
    ingresos_totales = EscrowTransaction.objects.filter(
        transaction_type='PLATFORM_FEE',
        status='RELEASED'
    ).aggregate(total=Sum('amount_usdc'))['total'] or Decimal('0.00')
    
    # 2. Usuarios Nuevos (últimos 30 días)
    hace_30_dias = timezone.now() - timedelta(days=30)
    usuarios_nuevos = UserProfile.objects.filter(
        fecha_creacion__gte=hace_30_dias
    ).count()
    
    # 3. Trabajos Activos
    trabajos_activos = JobOffer.objects.filter(status='IN_PROGRESS').count()
    
    # 4. % de Conflictos (trabajos con atrasos)
    total_trabajos = JobOffer.objects.filter(status='IN_PROGRESS').count()
    trabajos_conflicto = JobOffer.objects.filter(
        status='IN_PROGRESS',
        is_delayed=True
    ).count()
    
    if total_trabajos > 0:
        porcentaje_conflictos = (trabajos_conflicto / total_trabajos) * 100
    else:
        porcentaje_conflictos = 0.0
    
    
    # ========== GRÁFICO DE CRECIMIENTO (últimas 12 semanas) ==========
    semanas_labels = []
    semanas_valores = []
    
    for i in range(11, -1, -1):  # Últimas 12 semanas
        fecha_inicio = timezone.now() - timedelta(weeks=i+1)
        fecha_fin = timezone.now() - timedelta(weeks=i)
        
        trabajos_semana = JobOffer.objects.filter(
            created_at__gte=fecha_inicio,
            created_at__lt=fecha_fin
        ).count()
        
        semanas_labels.append(f"Semana {12-i}")
        semanas_valores.append(trabajos_semana)
    
    
    # ========== LISTA DE ALERTA (trabajos con más de 3 días de atraso) ==========
    trabajos_criticos = []
    
    trabajos_atrasados = JobOffer.objects.filter(
        status='IN_PROGRESS',
        is_delayed=True
    ).select_related('creator').prefetch_related('bids')
    
    for job in trabajos_atrasados:
        dias_atraso = job.get_days_delayed()
        
        if dias_atraso > 3:
            # Obtener el profesional (oficio) asignado
            bid_ganadora = job.bids.filter(is_winner=True).select_related('professional').first()
            
            trabajos_criticos.append({
                'job': job,
                'dias_atraso': dias_atraso,
                'profesional': bid_ganadora.professional if bid_ganadora else None,
            })
    
    # Ordenar por días de atraso (descendente)
    trabajos_criticos.sort(key=lambda x: x['dias_atraso'], reverse=True)
    
    
    # ========== ADMIN DE USUARIOS ==========
    # Búsqueda de usuarios (si hay query)
    search_query = request.GET.get('search', '').strip()
    usuarios_encontrados = []
    
    if search_query:
        usuarios_encontrados = UserProfile.objects.filter(
            Q(user__username__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query)
        ).select_related('user')[:20]
    
    
    # ========== ESTADÍSTICAS ADICIONALES ==========
    # Total de usuarios por rol
    usuarios_por_rol = {}
    for rol in ['PERSONA', 'CONSORCIO', 'OFICIO']:
        usuarios_por_rol[rol] = UserProfile.objects.filter(tipo_rol=rol).count()
    
    # Total de trabajos por estado
    trabajos_por_estado = {
        'OPEN': JobOffer.objects.filter(status='OPEN').count(),
        'IN_PROGRESS': JobOffer.objects.filter(status='IN_PROGRESS').count(),
        'CLOSED': JobOffer.objects.filter(status='CLOSED').count(),
    }
    
    
    context = {
        # Indicadores principales
        'ingresos_totales': ingresos_totales,
        'usuarios_nuevos': usuarios_nuevos,
        'trabajos_activos': trabajos_activos,
        'porcentaje_conflictos': round(porcentaje_conflictos, 1),
        'trabajos_conflicto': trabajos_conflicto,
        
        # Gráfico de crecimiento
        'semanas_labels': semanas_labels,
        'semanas_valores': semanas_valores,
        
        # Lista de alerta
        'trabajos_criticos': trabajos_criticos[:20],  # Máximo 20
        
        # Admin de usuarios
        'search_query': search_query,
        'usuarios_encontrados': usuarios_encontrados,
        
        # Stats adicionales
        'usuarios_por_rol': usuarios_por_rol,
        'trabajos_por_estado': trabajos_por_estado,
        
        # Fecha del reporte
        'fecha_reporte': timezone.now(),
    }
    
    return render(request, 'analytics/admin_dashboard.html', context)


@user_passes_test(lambda u: u.is_superuser)
def banear_usuario(request, user_id):
    """Banea (desactiva) un usuario."""
    if request.method == 'POST':
        try:
            profile = UserProfile.objects.get(id=user_id)
            profile.user.is_active = False
            profile.user.save()
            messages.success(request, f'Usuario {profile.user.username} baneado exitosamente.')
        except UserProfile.DoesNotExist:
            messages.error(request, 'Usuario no encontrado.')
    
    return redirect('analytics:admin_dashboard')


@user_passes_test(lambda u: u.is_superuser)
def verificar_cuit(request, user_id):
    """Marca un usuario como verificado (placeholder para verificación de CUIT)."""
    if request.method == 'POST':
        try:
            profile = UserProfile.objects.get(id=user_id)
            # Aquí podrías agregar un campo 'cuit_verificado' en el modelo
            messages.success(request, f'CUIT de {profile.user.username} verificado exitosamente.')
        except UserProfile.DoesNotExist:
            messages.error(request, 'Usuario no encontrado.')
    
    return redirect('analytics:admin_dashboard')


@user_passes_test(lambda u: u.is_superuser)
def generar_reporte_mensual_csv(request):
    """
    Genera un reporte CSV con todas las actividades del último mes.
    """
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    timestamp = timezone.now().strftime('%Y%m')
    response['Content-Disposition'] = f'attachment; filename="reporte_mensual_{timestamp}.csv"'
    
    response.write('\ufeff')
    
    writer = csv.writer(response, delimiter=';', quoting=csv.QUOTE_ALL)
    
    # Encabezados
    writer.writerow([
        'Fecha',
        'Tipo de Actividad',
        'Usuario',
        'Detalles',
        'Monto (USDC)',
        'Estado',
    ])
    
    # Obtener datos del último mes
    hace_30_dias = timezone.now() - timedelta(days=30)
    
    # Transacciones escrow
    transacciones = EscrowTransaction.objects.filter(
        created_at__gte=hace_30_dias
    ).select_related('job', 'from_wallet', 'to_wallet').order_by('-created_at')
    
    for tx in transacciones:
        writer.writerow([
            tx.created_at.strftime('%Y-%m-%d %H:%M'),
            'Transacción Escrow',
            tx.from_wallet.user.username if tx.from_wallet else '',
            f"{tx.get_transaction_type_display()} - {tx.job.title if tx.job else ''}",
            f"{tx.amount_usdc:.2f}",
            tx.get_status_display(),
        ])
    
    # Trabajos creados
    trabajos = JobOffer.objects.filter(
        created_at__gte=hace_30_dias
    ).select_related('creator').order_by('-created_at')
    
    for job in trabajos:
        writer.writerow([
            job.created_at.strftime('%Y-%m-%d %H:%M'),
            'Trabajo Creado',
            job.creator.user.username,
            job.title,
            f"{job.budget_base_ars:.2f}",
            job.get_status_display(),
        ])
    
    # Usuarios registrados
    usuarios = UserProfile.objects.filter(
        fecha_creacion__gte=hace_30_dias
    ).select_related('user').order_by('-fecha_creacion')
    
    for profile in usuarios:
        writer.writerow([
            profile.fecha_creacion.strftime('%Y-%m-%d %H:%M'),
            'Usuario Registrado',
            profile.user.username,
            f"{profile.get_tipo_rol_display()}",
            '0.00',
            'Activo' if profile.user.is_active else 'Inactivo',
        ])
    
    return response


@user_passes_test(lambda u: u.is_superuser)
def generar_reporte_csv(request):
    """
    Genera un archivo CSV descargable con todas las transacciones del sistema.
    
    Incluye:
    - ID de transacción
    - Fecha
    - Tipo de transacción
    - Trabajo asociado
    - Cliente (con CUIT si está disponible)
    - Profesional (con CUIT si está disponible)
    - Monto en USDC
    - Monto de comisión (5% para PLATFORM_FEE)
    - Estado
    """
    
    # Crear respuesta HTTP con tipo CSV
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    response['Content-Disposition'] = f'attachment; filename="reporte_transacciones_{timestamp}.csv"'
    
    # BOM para Excel (soporte UTF-8)
    response.write('\ufeff')
    
    # Crear writer CSV
    writer = csv.writer(response, delimiter=';', quoting=csv.QUOTE_ALL)
    
    # Encabezados
    writer.writerow([
        'ID Transacción',
        'Fecha',
        'Tipo de Transacción',
        'Estado',
        'ID Trabajo',
        'Título Trabajo',
        'Cliente',
        'CUIT/DNI Cliente',
        'Email Cliente',
        'Profesional',
        'CUIT/DNI Profesional',
        'Email Profesional',
        'Monto (USDC)',
        'Comisión Plataforma (USDC)',
        'Comisión %',
        'Wallet Origen',
        'Wallet Destino',
        'Descripción',
    ])
    
    # Obtener todas las transacciones de escrow
    transacciones = EscrowTransaction.objects.select_related(
        'job',
        'job__creator',
        'job__creator__user',
        'bid',
        'bid__professional',
        'bid__professional__user',
        'from_wallet',
        'from_wallet__user',
        'to_wallet',
        'to_wallet__user'
    ).order_by('-created_at')
    
    # Escribir filas
    for tx in transacciones:
        # Calcular comisión (solo para PLATFORM_FEE)
        if tx.transaction_type == 'PLATFORM_FEE':
            comision_monto = tx.amount_usdc
            comision_porcentaje = '5%'
        else:
            comision_monto = Decimal('0.00')
            comision_porcentaje = '0%'
        
        # Obtener información del cliente
        cliente_nombre = ''
        cliente_cuit = 'N/A'
        cliente_email = ''
        if tx.job and tx.job.creator:
            cliente_nombre = tx.job.creator.nombre_completo
            cliente_email = tx.job.creator.email
            # CUIT/DNI: buscar en el username o campos adicionales
            # (Nota: si tienes un campo específico para CUIT, úsalo aquí)
            cliente_cuit = f"Usuario: {tx.job.creator.user.username}"
        
        # Obtener información del profesional
        profesional_nombre = ''
        profesional_cuit = 'N/A'
        profesional_email = ''
        if tx.bid and tx.bid.professional:
            profesional_nombre = tx.bid.professional.nombre_completo
            profesional_email = tx.bid.professional.email
            profesional_cuit = f"Usuario: {tx.bid.professional.user.username}"
        
        # Información de wallets
        wallet_origen = ''
        if tx.from_wallet:
            wallet_origen = f"{tx.from_wallet.user.username} (ID: {tx.from_wallet.id})"
        
        wallet_destino = ''
        if tx.to_wallet:
            wallet_destino = f"{tx.to_wallet.user.username} (ID: {tx.to_wallet.id})"
        
        writer.writerow([
            tx.id,
            tx.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            tx.get_transaction_type_display(),
            tx.get_status_display(),
            tx.job.id if tx.job else '',
            tx.job.title if tx.job else '',
            cliente_nombre,
            cliente_cuit,
            cliente_email,
            profesional_nombre,
            profesional_cuit,
            profesional_email,
            f"{tx.amount_usdc:.2f}",
            f"{comision_monto:.2f}",
            comision_porcentaje,
            wallet_origen,
            wallet_destino,
            tx.description or '',
        ])
    
    return response


@user_passes_test(lambda u: u.is_superuser)
def generar_reporte_comisiones_csv(request):
    """
    Genera un reporte CSV específico de comisiones de la plataforma.
    
    Incluye solo las transacciones de tipo PLATFORM_FEE con información fiscal.
    """
    
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    response['Content-Disposition'] = f'attachment; filename="reporte_comisiones_{timestamp}.csv"'
    
    response.write('\ufeff')
    
    writer = csv.writer(response, delimiter=';', quoting=csv.QUOTE_ALL)
    
    # Encabezados para facturación
    writer.writerow([
        'Fecha de Facturación',
        'ID Transacción',
        'ID Trabajo',
        'Título del Trabajo',
        'Cliente - Razón Social',
        'Cliente - CUIT/DNI',
        'Cliente - Email',
        'Profesional - Razón Social',
        'Profesional - CUIT/DNI',
        'Profesional - Email',
        'Monto Base del Trabajo (USDC)',
        'Comisión Plataforma (USDC)',
        'Comisión %',
        'Estado de Pago',
        'Fecha de Pago',
        'Observaciones',
    ])
    
    # Obtener solo comisiones
    comisiones = EscrowTransaction.objects.filter(
        transaction_type='PLATFORM_FEE'
    ).select_related(
        'job',
        'job__creator',
        'job__creator__user',
        'bid',
        'bid__professional',
        'bid__professional__user'
    ).order_by('-created_at')
    
    for comision in comisiones:
        # Obtener el monto base del trabajo (70% del total, ya que la comisión es 5% de eso)
        monto_base = comision.amount_usdc * Decimal('14')  # 5% -> 100%, entonces multiplicar por 20
        
        cliente_nombre = comision.job.creator.nombre_completo if comision.job else ''
        cliente_cuit = f"Usuario: {comision.job.creator.user.username}" if comision.job else 'N/A'
        cliente_email = comision.job.creator.email if comision.job else ''
        
        profesional_nombre = comision.bid.professional.nombre_completo if comision.bid else ''
        profesional_cuit = f"Usuario: {comision.bid.professional.user.username}" if comision.bid else 'N/A'
        profesional_email = comision.bid.professional.email if comision.bid else ''
        
        estado_pago = 'PAGADO' if comision.status == 'RELEASED' else 'PENDIENTE'
        fecha_pago = comision.released_at.strftime('%Y-%m-%d %H:%M:%S') if comision.released_at else ''
        
        writer.writerow([
            comision.created_at.strftime('%Y-%m-%d'),
            comision.id,
            comision.job.id if comision.job else '',
            comision.job.title if comision.job else '',
            cliente_nombre,
            cliente_cuit,
            cliente_email,
            profesional_nombre,
            profesional_cuit,
            profesional_email,
            f"{monto_base:.2f}",
            f"{comision.amount_usdc:.2f}",
            '5%',
            estado_pago,
            fecha_pago,
            comision.description or '',
        ])
    
    return response
