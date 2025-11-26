from django.core.management.base import BaseCommand
from core.models import Turno
from datetime import date

class Command(BaseCommand):
    help = 'Actualiza automáticamente los turnos vencidos a NO_REALIZADA'

    def handle(self, *args, **kwargs):
        hoy = date.today()
        
        # Buscar turnos confirmados cuya fecha ya pasó (menor a hoy)
        turnos_vencidos = Turno.objects.filter(
            agenda__fecha__lt=hoy,
            estado='CONFIRMADO'
        )
        
        count = 0
        for turno in turnos_vencidos:
            turno.estado = 'NO_REALIZADA'
            turno.observaciones = (turno.observaciones or "") + " [SISTEMA: Marcado como NO REALIZADA por fecha vencida sin formulario]"
            turno.save()
            count += 1
            
        self.stdout.write(self.style.SUCCESS(f"Proceso completado. {count} turnos marcados como NO_REALIZADA."))