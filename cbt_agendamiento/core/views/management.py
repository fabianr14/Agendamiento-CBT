from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, ProtectedError
from django.contrib.auth.models import User
from django.contrib.gis.geos import Point
from datetime import date
from django.db import transaction

from ..forms import (
    AltaContribuyenteForm, TipoEstablecimientoForm, EditarUsuarioForm, NuevoInspectorForm
)
from ..models import (
    Establecimiento, TipoEstablecimiento, AgendaDiaria, Turno, OPCIONES_PARROQUIA, Notificacion
)

def es_staff(user): return user.is_staff
def es_superuser(user): return user.is_superuser

# --- VENTANILLA ---
@login_required
@user_passes_test(es_staff)
def buscar_local_presencial(request):
    query = request.GET.get('q')
    locales = []
    if query:
        locales = Establecimiento.objects.filter(
            Q(propietario__perfil__ruc__icontains=query) |
            Q(nombre_comercial__icontains=query)
        )[:10]
    return render(request, 'staff/buscar_local.html', {'locales': locales, 'query': query})

@login_required
@user_passes_test(es_staff)
def agendar_presencial_detalle(request, local_id):
    local = get_object_or_404(Establecimiento, id=local_id)
    
    # Validación de turno activo
    turno_activo = Turno.objects.filter(establecimiento=local, estado__in=['PENDIENTE', 'CONFIRMADO'], agenda__fecha__gte=date.today()).first()
    if turno_activo:
        return render(request, 'staff/agendar_presencial.html', {'local': local, 'turno_activo': turno_activo, 'opciones': None})

    agendas = AgendaDiaria.objects.filter(parroquia_destino=local.parroquia, fecha__gte=date.today(), cupos_habilitados=True).order_by('fecha')

    if request.method == 'POST':
        with transaction.atomic():
            agenda = AgendaDiaria.objects.select_for_update().get(id=request.POST.get('agenda_id'))
            bloque = request.POST.get('bloque')
            
            ocupados = Turno.objects.filter(agenda=agenda, bloque=bloque).exclude(estado='CANCELADO').count()
            cap = agenda.capacidad_manana if bloque == 'MANANA' else agenda.capacidad_tarde
            
            if ocupados >= cap:
                messages.error(request, "Cupo lleno.")
                return redirect('agendar_presencial_detalle', local_id=local.id)

            Turno.objects.create(
                agenda=agenda, establecimiento=local, bloque=bloque, estado='CONFIRMADO',
                inspector=request.user, observaciones="VENTANILLA",
                telefono_contacto=request.POST.get('telefono'), referencia_ubicacion=request.POST.get('referencia')
            )
            
            Notificacion.objects.create(
                usuario=local.propietario, titulo="Turno Asignado ✅",
                mensaje=f"Confirmado turno presencial.", tipo="SUCCESS", link="/portal/"
            )
            messages.success(request, "Confirmado.")
            return redirect('dashboard_staff')

    opciones = []
    for ag in agendas:
        ocup_man = Turno.objects.filter(agenda=ag, bloque='MANANA').exclude(estado='CANCELADO').count()
        ocup_tar = Turno.objects.filter(agenda=ag, bloque='TARDE').exclude(estado='CANCELADO').count()
        
        bloques = []
        if ocup_man < ag.capacidad_manana:
            bloques.append({'codigo': 'MANANA', 'label': 'MAÑANA', 'pct': int((ocup_man/ag.capacidad_manana)*100), 'ocupados': ocup_man, 'total': ag.capacidad_manana, 'hora': '09:00'})
        if ocup_tar < ag.capacidad_tarde:
            bloques.append({'codigo': 'TARDE', 'label': 'TARDE', 'pct': int((ocup_tar/ag.capacidad_tarde)*100), 'ocupados': ocup_tar, 'total': ag.capacidad_tarde, 'hora': '14:45'})
            
        if bloques: opciones.append({'info': ag, 'bloques': bloques})

    return render(request, 'staff/agendar_presencial.html', {'local': local, 'opciones': opciones})

# --- ALTA Y DIRECTORIO ---
@login_required
@user_passes_test(es_staff)
def alta_contribuyente(request):
    if request.method == 'POST':
        form = AltaContribuyenteForm(request.POST)
        if form.is_valid():
            form.save(); messages.success(request, "Registrado."); return redirect('dashboard_staff')
    else: form = AltaContribuyenteForm()
    return render(request, 'staff/alta_contribuyente.html', {'form': form})

@login_required
@user_passes_test(es_staff)
def directorio_establecimientos(request):
    query = request.GET.get('q', '')
    filtro = request.GET.get('tipo', '')
    locales = Establecimiento.objects.all().order_by('nombre_comercial')
    
    if query:
        locales = locales.filter(Q(nombre_comercial__icontains=query) | Q(propietario__perfil__ruc__icontains=query))
    if filtro:
        locales = locales.filter(tipo_id=filtro)
        
    return render(request, 'staff/directorio.html', {'locales': locales, 'tipos': TipoEstablecimiento.objects.all(), 'query': query, 'filtro_tipo': int(filtro) if filtro else ''})

@login_required
@user_passes_test(es_staff)
def detalle_establecimiento(request, local_id):
    local = get_object_or_404(Establecimiento, id=local_id)
    historial = Turno.objects.filter(establecimiento=local).order_by('-agenda__fecha')
    
    if request.method == 'POST':
        local.nombre_comercial = request.POST.get('nombre_comercial').upper()
        local.razon_social = request.POST.get('razon_social').upper()
        local.direccion = request.POST.get('direccion').upper()
        local.parroquia = request.POST.get('parroquia')
        if request.POST.get('tipo'): local.tipo_id = request.POST.get('tipo')
        
        lat = request.POST.get('latitud')
        lon = request.POST.get('longitud')
        if lat and lon:
            try: local.ubicacion = Point(float(lon), float(lat), srid=4326); local.ubicacion_verificada = True 
            except: pass

        local.save(); messages.success(request, "Actualizado.")
        return redirect('detalle_establecimiento', local_id=local.id)

    return render(request, 'staff/detalle_local.html', {'local': local, 'historial': historial, 'tipos': TipoEstablecimiento.objects.all(), 'parroquias': OPCIONES_PARROQUIA})

# --- USUARIOS Y TIPOS ---
@login_required
@user_passes_test(es_staff)
def gestion_usuarios(request):
    query = request.GET.get('q', '')
    
    if request.user.is_superuser:
        usuarios = User.objects.exclude(pk=request.user.pk)
    else:
        usuarios = User.objects.filter(is_staff=False, is_superuser=False)
    
    if query:
        usuarios = usuarios.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query) |
            Q(perfil__ruc__icontains=query) |
            Q(perfil__telefono__icontains=query)
        ).distinct()

    usuarios = usuarios.order_by('-date_joined')
    return render(request, 'staff/gestion_usuarios.html', {'usuarios': usuarios, 'query': query})

@login_required
@user_passes_test(es_staff)
def detalle_usuario(request, user_id):
    usuario = get_object_or_404(User, pk=user_id)
    locales = usuario.establecimientos.all()
    return render(request, 'staff/detalle_usuario.html', {'usuario': usuario, 'locales': locales})

@login_required
@user_passes_test(es_staff)
def editar_usuario(request, user_id):
    usuario = get_object_or_404(User, pk=user_id)
    
    if not request.user.is_superuser and (usuario.is_staff or usuario.is_superuser):
         messages.error(request, "No tiene permisos para editar a este usuario.")
         return redirect('gestion_usuarios')

    if request.method == 'POST':
        form = EditarUsuarioForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, "Usuario actualizado.")
            return redirect('detalle_usuario', user_id=usuario.id)
    else:
        form = EditarUsuarioForm(instance=usuario)
    return render(request, 'staff/editar_usuario.html', {'form': form, 'usuario': usuario})

@login_required
@user_passes_test(es_staff)
def eliminar_usuario(request, user_id):
    usuario = get_object_or_404(User, pk=user_id)
    if not request.user.is_superuser and usuario.is_staff:
        messages.error(request, "Acción denegada.")
        return redirect('gestion_usuarios')
    try:
        usuario.delete()
        messages.success(request, "Usuario eliminado.")
    except ProtectedError:
        messages.error(request, "No se puede eliminar: Tiene registros vinculados.")
    return redirect('gestion_usuarios')

@login_required
@user_passes_test(es_superuser)
def cambiar_rol(request, user_id):
    usuario = get_object_or_404(User, pk=user_id)
    if usuario.pk == request.user.pk:
        messages.error(request, "No puedes cambiar tu propio rol.")
        return redirect('gestion_usuarios')
    if usuario.is_staff:
        usuario.is_staff = False
        msg = f"Rol de {usuario.username} cambiado a: CIUDADANO"
    else:
        usuario.is_staff = True
        msg = f"Rol de {usuario.username} cambiado a: INSPECTOR"
    usuario.save()
    messages.success(request, msg)
    return redirect('gestion_usuarios')

@login_required
@user_passes_test(es_superuser)
def crear_inspector(request):
    if request.method == 'POST':
        form = NuevoInspectorForm(request.POST)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Inspector registrado.")
                return redirect('gestion_usuarios')
            except Exception as e:
                messages.error(request, f"Error al registrar: {e}")
    else:
        form = NuevoInspectorForm()
    return render(request, 'staff/crear_inspector.html', {'form': form})

@login_required
@user_passes_test(es_staff)
def carga_masiva_locales(request):
    if request.method == 'POST':
        form = CargaMasivaForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = request.FILES['archivo_excel']
            
            try:
                wb = openpyxl.load_workbook(excel_file)
                ws = wb.active
                
                count_creados = 0
                count_actualizados = 0
                errores = []

                # Iterar filas (saltando la cabecera)
                for index, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
                    # Estructura esperada: 
                    # 0:CEDULA, 1:NOMBRES, 2:RUC, 3:RAZON, 4:COMERCIAL, 5:TIPO, 6:PARROQUIA_CODE, 7:DIRECCION, 8:TELEFONO
                    try:
                        cedula = str(row[0]).strip()
                        nombres = str(row[1]).upper().strip()
                        ruc = str(row[2]).strip()
                        razon = str(row[3]).upper().strip()
                        comercial = str(row[4]).upper().strip()
                        tipo_nombre = str(row[5]).upper().strip()
                        parroquia_code = str(row[6]).upper().strip() # Debe coincidir con los códigos (ej: TULCAN_CENTRO)
                        direccion = str(row[7]).upper().strip()
                        telefono = str(row[8]).strip() if row[8] else ""

                        # 1. Usuario
                        user, created = User.objects.get_or_create(username=cedula)
                        if created:
                            user.set_password(cedula)
                        user.first_name = nombres
                        user.save()

                        # 2. Perfil
                        if hasattr(user, 'perfil'):
                            user.perfil.ruc = ruc
                            user.perfil.telefono = telefono
                            user.perfil.save()
                        else:
                            PerfilUsuario.objects.create(user=user, ruc=ruc, telefono=telefono)

                        # 3. Tipo Local (Buscar o Crear)
                        tipo_obj, _ = TipoEstablecimiento.objects.get_or_create(nombre=tipo_nombre)

                        # 4. Establecimiento
                        local, created_local = Establecimiento.objects.update_or_create(
                            propietario=user,
                            nombre_comercial=comercial,
                            defaults={
                                'razon_social': razon,
                                'tipo': tipo_obj,
                                'parroquia': parroquia_code,
                                'direccion': direccion,
                                # Dejamos ubicacion en None para que el usuario la ponga luego
                            }
                        )

                        if created_local: count_creados += 1
                        else: count_actualizados += 1

                    except Exception as e:
                        errores.append(f"Fila {index}: {str(e)}")

                # Resumen
                if count_creados > 0 or count_actualizados > 0:
                    messages.success(request, f"Proceso terminado: {count_creados} nuevos, {count_actualizados} actualizados.")
                
                if errores:
                    messages.warning(request, f"Hubo {len(errores)} errores. Revise el formato.")
                
                return redirect('directorio_establecimientos')

            except Exception as e:
                messages.error(request, f"Error leyendo el archivo: {e}")

    else:
        form = CargaMasivaForm()

    return render(request, 'staff/carga_masiva.html', {'form': form})