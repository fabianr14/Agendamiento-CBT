from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.contrib.auth.models import User
from django.contrib.gis.geos import Point
from datetime import date, timedelta

from ..models import (
    Establecimiento, Turno, AgendaDiaria, PerfilUsuario, Notificacion
)
from ..forms import RegistroEmailForm, MiPerfilForm

@login_required
def home_ciudadano(request):
    if request.user.is_staff:
        return redirect('dashboard_staff')

    # 1. Onboarding: Email
    if not request.user.email:
        messages.warning(request, "Paso 1: Registro de Correo Electrónico requerido.")
        return redirect('registrar_email')

    mis_locales = request.user.establecimientos.all()
    
    # 2. Onboarding: Mapa
    for local in mis_locales:
        if not local.ubicacion_verificada:
            total = mis_locales.filter(ubicacion_verificada=False).count()
            msg = f"¡Atención! Tiene {total} locales pendientes de ubicación. Configure '{local.nombre_comercial}'."
            messages.info(request, msg)
            return redirect('verificar_ubicacion', local_id=local.id)

    # 3. Dashboard
    today = date.today()
    
    selected_id = request.GET.get('local_id')
    selected_local = mis_locales.filter(id=selected_id).first() if selected_id else mis_locales.first()
    
    turnos_activos = Turno.objects.filter(
        establecimiento__in=mis_locales,
        agenda__fecha__gte=today
    ).exclude(estado='RECHAZADO').order_by('agenda__fecha')
    
    historial = []
    if selected_local:
        historial = Turno.objects.filter(
            establecimiento=selected_local
        ).exclude(id__in=turnos_activos).order_by('-agenda__fecha')

    return render(request, 'ciudadano/home.html', {
        'locales': mis_locales,
        'selected_local': selected_local,
        'turnos_activos': turnos_activos,
        'historial': historial
    })

@login_required
def registrar_email(request):
    if request.user.email: return redirect('home_ciudadano')
    if request.method == 'POST':
        form = RegistroEmailForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "¡Correo registrado!")
            return redirect('home_ciudadano')
    else:
        form = RegistroEmailForm(instance=request.user)
    return render(request, 'ciudadano/registrar_email.html', {'form': form})

@login_required
def verificar_ubicacion(request, local_id):
    local = get_object_or_404(Establecimiento, id=local_id, propietario=request.user)
    if request.method == 'POST':
        lat = request.POST.get('latitud')
        lon = request.POST.get('longitud')
        if lat and lon:
            try:
                local.ubicacion = Point(float(lon), float(lat), srid=4326)
                local.ubicacion_verificada = True
                local.save()
                
                restantes = request.user.establecimientos.filter(ubicacion_verificada=False).exists()
                if restantes:
                    messages.success(request, "Ubicación guardada. Siguiente local...")
                else:
                    messages.success(request, "¡Todo listo! Locales configurados.")
                    
                return redirect('home_ciudadano')
            except ValueError:
                messages.error(request, "Error en coordenadas.")
        else:
            messages.error(request, "Por favor, fije su ubicación en el mapa.")

    return render(request, 'ciudadano/verificar_ubicacion.html', {'local': local})

@login_required
def detalle_local_ciudadano(request, local_id):
    local = get_object_or_404(Establecimiento, id=local_id, propietario=request.user)
    historial = Turno.objects.filter(establecimiento=local).order_by('-agenda__fecha')
    return render(request, 'ciudadano/detalle_local.html', {
        'local': local, 
        'historial': historial
    })

@login_required
def agendar_turno(request):
    local_id = request.GET.get('local_id')
    # Protección: Solo el dueño puede agendar
    local = get_object_or_404(Establecimiento, id=local_id, propietario=request.user)

    # Validación: ¿Ya tiene turno activo?
    turno_activo = Turno.objects.filter(
        establecimiento=local,
        estado__in=['PENDIENTE', 'CONFIRMADO'],
        agenda__fecha__gte=date.today()
    ).first()
    
    if turno_activo:
        messages.warning(request, f"Este local ya tiene una solicitud activa para el {turno_activo.agenda.fecha}.")
        return redirect('home_ciudadano')

    agendas = AgendaDiaria.objects.filter(
        parroquia_destino=local.parroquia,
        fecha__gte=date.today(),
        cupos_habilitados=True
    ).order_by('fecha')

    if request.method == 'POST':
        agenda_id = request.POST.get('agenda_id')
        bloque = request.POST.get('bloque')
        telefono = request.POST.get('telefono')
        referencia = request.POST.get('referencia')
        
        # Transacción para evitar sobreventa de cupos
        with transaction.atomic():
            agenda = AgendaDiaria.objects.select_for_update().get(id=agenda_id)
            
            ocupados = Turno.objects.filter(agenda=agenda, bloque=bloque).count()
            cap = agenda.capacidad_manana if bloque == 'MANANA' else agenda.capacidad_tarde
            
            if ocupados >= cap:
                messages.error(request, "❌ Cupo lleno. Intente otra fecha.")
                return redirect(f"/portal/agendar/?local_id={local.id}")
            
            Turno.objects.create(
                agenda=agenda,
                establecimiento=local,
                bloque=bloque,
                telefono_contacto=telefono,
                referencia_ubicacion=referencia,
                estado='PENDIENTE'
            )
            
            # Notificar Staff
            for insp in User.objects.filter(is_staff=True):
                Notificacion.objects.create(
                    usuario=insp,
                    titulo="Nueva Solicitud 📥",
                    mensaje=f"{local.nombre_comercial} solicitó turno.",
                    tipo="INFO",
                    link="/panel-operativo/"
                )

            messages.success(request, "Solicitud enviada.")
            return redirect('home_ciudadano')

    # Calcular disponibilidad para la vista
    opciones = []
    for ag in agendas:
        ocup_manana = Turno.objects.filter(agenda=ag, bloque='MANANA').exclude(estado='CANCELADO').count()
        ocup_tarde = Turno.objects.filter(agenda=ag, bloque='TARDE').exclude(estado='CANCELADO').count()
        
        pct_manana = int((ocup_manana / ag.capacidad_manana) * 100) if ag.capacidad_manana > 0 else 100
        pct_tarde = int((ocup_tarde / ag.capacidad_tarde) * 100) if ag.capacidad_tarde > 0 else 100
        
        bloques = []
        if ocup_manana < ag.capacidad_manana:
            bloques.append({'codigo': 'MANANA', 'label': 'MAÑANA', 'hora': '09:00 - 12:30', 'ocupados': ocup_manana, 'total': ag.capacidad_manana, 'pct': pct_manana})
        if ocup_tarde < ag.capacidad_tarde:
            bloques.append({'codigo': 'TARDE', 'label': 'TARDE', 'hora': '14:45 - 16:30', 'ocupados': ocup_tarde, 'total': ag.capacidad_tarde, 'pct': pct_tarde})
            
        if bloques:
            opciones.append({'info': ag, 'bloques': bloques})

    return render(request, 'ciudadano/agendar.html', {
        'opciones': opciones,
        'local': local
    })

@login_required
def cancelar_turno(request, turno_id):
    turno = get_object_or_404(Turno, id=turno_id)
    
    if not request.user.is_staff and turno.establecimiento.propietario != request.user:
        messages.error(request, "No tiene permiso.")
        return redirect('home_ciudadano')

    # Regla: Solo hasta un día antes
    if turno.agenda.fecha <= date.today():
        messages.error(request, "No se puede cancelar el mismo día de la inspección.")
        if request.user.is_staff: return redirect('dashboard_staff')
        return redirect('home_ciudadano')

    turno.estado = 'CANCELADO'
    turno.save()
    
    if request.user.is_staff:
        Notificacion.objects.create(
            usuario=turno.establecimiento.propietario,
            titulo="Turno Cancelado",
            mensaje=f"Su turno para {turno.establecimiento.nombre_comercial} ha sido cancelado.",
            tipo="WARNING"
        )
    
    messages.success(request, "El turno ha sido cancelado.")
    
    if request.user.is_staff: return redirect('dashboard_staff')
    return redirect('home_ciudadano')

@login_required
def mi_perfil(request):
    user = request.user
    perfil = getattr(user, 'perfil', None)
    
    dias = 0
    puede = True
    
    if perfil and perfil.fecha_ultima_actualizacion:
        f_unlock = perfil.fecha_ultima_actualizacion + timedelta(days=90)
        if date.today() < f_unlock:
            puede = False
            dias = (f_unlock - date.today()).days
    
    if request.method == 'POST':
        if not puede and not user.is_superuser:
            messages.error(request, f"Edición bloqueada. Espere {dias} días.")
            return redirect('mi_perfil')
            
        form = MiPerfilForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Perfil actualizado.")
            return redirect('mi_perfil')
    else:
        form = MiPerfilForm(instance=user)

    extra = {'puede_editar': puede, 'dias_restantes': dias}
    if user.is_staff:
        extra['total_inspecciones'] = Turno.objects.filter(inspector=user, estado='CONFIRMADO').count()
        extra['tipo_usuario'] = 'INSPECTOR'
    else:
        extra['locales'] = user.establecimientos.all()
        extra['tipo_usuario'] = 'CIUDADANO'

    return render(request, 'perfil.html', {'form': form, **extra})
@login_required
def ver_tasas_impuestos(request):
    """
    Renderiza el cuadro tarifario oficial.
    """
    return render(request, 'ciudadano/docs/tasas.html', {
        'anio_fiscal': date.today().year
    })

@login_required
def ver_guia_requisitos(request):
    """
    Renderiza la guía de requisitos técnicos.
    """
    return render(request, 'ciudadano/docs/requisitos.html', {
        'anio_fiscal': date.today().year
    })