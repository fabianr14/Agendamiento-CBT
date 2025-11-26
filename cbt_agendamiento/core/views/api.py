from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from ..models import Notificacion, PerfilUsuario

@login_required
def api_buscar_propietario(request):
    cedula = request.GET.get('cedula')
    response = {
        'existe': False, 
        'nombres': '', 
        'ruc': '',
        'locales': [] # Nueva lista vacía por defecto
    }
    
    if cedula and len(cedula) >= 10:
        try:
            user = User.objects.get(username=cedula)
            response['existe'] = True
            response['nombres'] = user.first_name
            
            # RUC
            if hasattr(user, 'perfil'):
                response['ruc'] = user.perfil.ruc
            
            # BUSCAR LOCALES EXISTENTES
            # Usamos .values() para obtener solo los datos necesarios y enviarlos como JSON
            locales = user.establecimientos.all().values(
                'nombre_comercial', 
                'direccion', 
                'parroquia' # Esto devuelve el código (ej: TULCAN_CENTRO)
            )
            
            # Convertimos el QuerySet a una lista para que sea serializable
            response['locales'] = list(locales)

        except User.DoesNotExist:
            pass
            
    return JsonResponse(response)

@login_required
def api_mis_notificaciones(request):
    notificaciones = Notificacion.objects.filter(usuario=request.user, leido=False)[:5]
    data = []
    for n in notificaciones:
        data.append({
            'id': n.id,
            'titulo': n.titulo,
            'mensaje': n.mensaje,
            'tipo': n.tipo,
            'fecha': n.fecha_creacion.strftime("%H:%M"),
            'link': n.link
        })
    return JsonResponse({'count': len(data), 'notificaciones': data})

@login_required
def api_marcar_leida(request, notificacion_id):
    try:
        n = Notificacion.objects.get(id=notificacion_id, usuario=request.user)
        n.leido = True
        n.save()
        return JsonResponse({'status': 'ok'})
    except Notificacion.DoesNotExist:
        return JsonResponse({'status': 'error'}, status=404)