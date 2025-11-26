from django.core.management.base import BaseCommand
from core.models import Turno, Notificacion
from datetime import date

class Command(BaseCommand):
    help = 'Limpia turnos vencidos y actualiza estados automáticamente'

    def handle(self, *args, **kwargs):
        hoy = date.today()
        
        self.stdout.write("Iniciando limpieza de turnos vencidos...")

        # ---------------------------------------------------------
        # CASO 1: Solicitudes PENDIENTES que ya pasaron de fecha
        # ---------------------------------------------------------
        # Problema: El inspector nunca las revisó.
        # Acción: Rechazar automáticamente por caducidad.
        pendientes_vencidos = Turno.objects.filter(
            estado='PENDIENTE',
            agenda__fecha__lt=hoy
        )
        
        count_pend = 0
        for t in pendientes_vencidos:
            t.estado = 'RECHAZADO'
            t.observaciones = "SISTEMA: Solicitud caducada. La fecha solicitada pasó sin gestión del inspector."
            t.save()
            
            # Notificar al usuario para que no se quede esperando
            Notificacion.objects.create(
                usuario=t.establecimiento.propietario,
                titulo="Solicitud Caducada 🕒",
                mensaje=f"Su solicitud para el {t.agenda.fecha} expiró sin confirmación. Por favor agende nuevamente.",
                tipo="WARNING",
                link="/portal/"
            )
            count_pend += 1

        # ---------------------------------------------------------
        # CASO 2: Turnos CONFIRMADOS que ya pasaron de fecha
        # ---------------------------------------------------------
        # Problema: Se agendó, pero nadie reportó nada (Ni éxito, ni fracaso, ni ejecución).
        # Acción: Marcar como NO_REALIZADA (Ausente/Olvido).
        # NOTA CRÍTICA: NO tocamos los que están en estado 'EJECUTADA'.
        confirmados_vencidos = Turno.objects.filter(
            estado='CONFIRMADO',
            agenda__fecha__lt=hoy
        )
        
        count_conf = 0
        for t in confirmados_vencidos:
            # Cambiamos a NO_REALIZADA (que en tu modelo se visualiza como 'AUSENTE' o similar)
            t.estado = 'NO_REALIZADA' 
            t.observaciones = "SISTEMA: Cierre automático por falta de gestión del turno."
            t.save()
            
            # Notificación de Disculpa/Aviso
            Notificacion.objects.create(
                usuario=t.establecimiento.propietario,
                titulo="Inspección No Registrada ⚠️",
                mensaje=f"La visita del {t.agenda.fecha} no tiene registro de ejecución. Por favor solicite un nuevo turno.",
                tipo="ERROR",
                link="/portal/"
            )
            count_conf += 1

        self.stdout.write(self.style.SUCCESS(
            f"LIMPIEZA COMPLETA:\n"
            f"- {count_pend} Solicitudes caducadas (Rechazadas)\n"
            f"- {count_conf} Inspecciones abandonadas (No Realizadas)\n"
            f"* Las inspecciones en estado 'EJECUTADA' se mantuvieron intactas."
        ))