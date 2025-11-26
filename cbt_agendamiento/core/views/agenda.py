from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from datetime import date, datetime, timedelta
from ..models import AgendaDiaria, ConfiguracionSistema, OPCIONES_PARROQUIA
from ..forms import ConfiguracionGlobalForm, EdicionAgendaForm

def es_staff(user): return user.is_staff

@login_required
@user_passes_test(es_staff)
def habilitar_agenda(request):
    config, _ = ConfiguracionSistema.objects.get_or_create(solo_id=1)

    if request.method == 'POST':
        if 'actualizar_config' in request.POST:
            f = ConfiguracionGlobalForm(request.POST, instance=config)
            if f.is_valid(): f.save(); messages.success(request, "Configuración guardada.")
            
        elif 'crear_agenda' in request.POST:
            try:
                start = datetime.strptime(request.POST.get('fecha_inicio'), "%Y-%m-%d").date()
                end = datetime.strptime(request.POST.get('fecha_fin'), "%Y-%m-%d").date()
                zonas = request.POST.getlist('zonas')
                dias = request.POST.getlist('dias_semana')
                
                if start < date.today(): 
                    messages.error(request, "Fechas pasadas.")
                    return redirect('habilitar_agenda')

                count = 0
                for i in range((end - start).days + 1):
                    d = start + timedelta(days=i)
                    if str(d.weekday()) in dias:
                        for z in zonas:
                            _, created = AgendaDiaria.objects.get_or_create(
                                fecha=d, parroquia_destino=z,
                                defaults={'capacidad_manana': config.def_capacidad_manana, 'capacidad_tarde': config.def_capacidad_tarde, 'cupos_habilitados': True}
                            )
                            if created: count += 1
                messages.success(request, f"{count} fechas creadas.")
            except: messages.error(request, "Error en fechas.")
            return redirect('habilitar_agenda')

    zonas_u = [z for z in OPCIONES_PARROQUIA if z[0] in ['GONZALEZ_SUAREZ', 'TULCAN_CENTRO']]
    zonas_r = [z for z in OPCIONES_PARROQUIA if z[0] not in ['GONZALEZ_SUAREZ', 'TULCAN_CENTRO']]
    agendas = AgendaDiaria.objects.filter(fecha__gte=date.today()).order_by('fecha', 'parroquia_destino')
    
    return render(request, 'staff/habilitar_agenda.html', {
        'zonas_urbanas': zonas_u, 'zonas_rurales': zonas_r, 'agendas': agendas,
        'hoy_str': date.today().strftime("%Y-%m-%d"),
        'form_config': ConfiguracionGlobalForm(instance=config), 'config': config
    })

@login_required
@user_passes_test(es_staff)
def editar_agenda_detalle(request, agenda_id):
    agenda = get_object_or_404(AgendaDiaria, id=agenda_id)
    if request.method == 'POST':
        form = EdicionAgendaForm(request.POST, instance=agenda)
        if form.is_valid(): form.save(); messages.success(request, "Actualizado."); return redirect('habilitar_agenda')
    else: form = EdicionAgendaForm(instance=agenda)
    return render(request, 'staff/editar_agenda.html', {'form': form, 'agenda': agenda})