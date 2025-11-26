from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from core.models import Turno
from core.utils import enviar_sms 
from datetime import date

class Command(BaseCommand):
    help = 'Envía recordatorios por correo y SMS a las inspecciones de HOY'

    def handle(self, *args, **kwargs):
        hoy = date.today()
        self.stdout.write(f"--> Buscando inspecciones confirmadas para hoy: {hoy}")
        
        turnos_hoy = Turno.objects.filter(agenda__fecha=hoy, estado='CONFIRMADO')
        
        if not turnos_hoy:
            self.stdout.write(self.style.WARNING("No hay inspecciones confirmadas para hoy."))
            return

        count = 0
        for turno in turnos_hoy:
            # Datos de contacto
            # Usamos getattr para evitar error si el usuario no tiene email
            email = getattr(turno.establecimiento.propietario, 'email', None)
            
            # Prioridad teléfono: Turno > Perfil
            telefono = turno.telefono_contacto
            if not telefono and hasattr(turno.establecimiento.propietario, 'perfil'):
                telefono = turno.establecimiento.propietario.perfil.telefono
                
            local = turno.establecimiento.nombre_comercial
            jornada = turno.get_bloque_display()

            # 1. ENVIAR CORREO
            if email:
                try:
                    asunto = f"RECORDATORIO: Inspección HOY - {local}"
                    mensaje = f"""
                    Estimado usuario,
                    
                    Le recordamos que TIENE UNA INSPECCIÓN PROGRAMADA PARA HOY.
                    
                    Local: {local}
                    Jornada: {jornada}
                    
                    Por favor, asegúrese de que haya una persona encargada en el local.
                    """
                    send_mail(asunto, mensaje, 'sistema@bomberostulcan.gob.ec', [email], fail_silently=True)
                    self.stdout.write(f"   - Email enviado a {email}")
                except: pass

            # 2. ENVIAR SMS
            if telefono:
                try:
                    msg_sms = f"RECORDATORIO CBT: Hoy tiene inspeccion en {local}. Horario: {jornada}. Por favor estar presente."
                    # Enviamos el SMS usando la utilidad
                    enviar_sms(telefono, msg_sms)
                    self.stdout.write(f"   - SMS enviado a {telefono}")
                    count += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"   - Error SMS: {e}"))
        
        self.stdout.write(self.style.SUCCESS(f"Proceso terminado. {count} notificaciones procesadas."))