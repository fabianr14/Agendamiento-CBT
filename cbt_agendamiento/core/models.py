from django.db import models
from django.contrib.auth.models import User
from django.contrib.gis.db import models as gis_models
from django.db.models import Max, F

# ==============================================================================
#                              USUARIOS Y PERFILES
# ==============================================================================

class PerfilUsuario(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    ruc = models.CharField(max_length=13, unique=True, verbose_name="RUC")
    telefono = models.CharField(max_length=15, verbose_name="Teléfono", null=True, blank=True)
    fecha_ultima_actualizacion = models.DateField(null=True, blank=True)
    def __str__(self): return f"Perfil de {self.user.username}"

# ==============================================================================
#                              CATÁLOGOS
# ==============================================================================

class TipoEstablecimiento(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    def save(self, *args, **kwargs):
        self.nombre = self.nombre.upper().strip()
        super().save(*args, **kwargs)
    def __str__(self): return self.nombre

OPCIONES_PARROQUIA = [
    ('GONZALEZ_SUAREZ', 'URBANA: GONZÁLEZ SUÁREZ (NORTE)'),
    ('TULCAN_CENTRO',   'URBANA: TULCÁN (CENTRO/SUR)'),
    ('MALDONADO', 'RURAL: MALDONADO'),
    ('CHICAL', 'RURAL: CHICAL'),
    ('TOBAR DONOSO', 'RURAL: TOBAR DONOSO'),
    ('EL CARMELO', 'RURAL: EL CARMELO'),
    ('URBINA', 'RURAL: URBINA'),
    ('JULIO ANDRADE', 'RURAL: JULIO ANDRADE'),
    ('PIOTER', 'RURAL: PIOTER'),
    ('SANTA MARTHA', 'RURAL: SANTA MARTHA DE CUBA'),
    ('TUFIÑO', 'RURAL: TUFIÑO'),
]
class ConfiguracionSistema(models.Model):
    solo_id = models.IntegerField(default=1, unique=True, editable=False)
    def_capacidad_manana = models.PositiveIntegerField(default=6, verbose_name="Defecto Mañana")
    def_capacidad_tarde = models.PositiveIntegerField(default=4, verbose_name="Defecto Tarde")
    def save(self, *args, **kwargs):
        self.solo_id = 1 
        super().save(*args, **kwargs)
    def __str__(self): return "Configuración Global CBT"

# ==============================================================================
#                              NEGOCIO PRINCIPAL
# ==============================================================================

class Establecimiento(models.Model):
    propietario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='establecimientos')
    razon_social = models.CharField(max_length=255, verbose_name="Razón Social")
    nombre_comercial = models.CharField(max_length=255, verbose_name="Nombre Comercial")
    tipo = models.ForeignKey(TipoEstablecimiento, on_delete=models.PROTECT, verbose_name="Giro de Negocio")
    direccion = models.CharField(max_length=255, verbose_name="Dirección")
    parroquia = models.CharField(max_length=50, choices=OPCIONES_PARROQUIA)
    ubicacion = gis_models.PointField(srid=4326, null=True, blank=True) 
    ubicacion_verificada = models.BooleanField(default=False, verbose_name="Ubicación Confirmada por Usuario")
    def save(self, *args, **kwargs):
        self.razon_social = self.razon_social.upper().strip()
        self.nombre_comercial = self.nombre_comercial.upper().strip()
        self.direccion = self.direccion.upper().strip()
        super().save(*args, **kwargs)
    def __str__(self): return self.nombre_comercial

class AgendaDiaria(models.Model):
    fecha = models.DateField()
    parroquia_destino = models.CharField(max_length=50, choices=OPCIONES_PARROQUIA)
    capacidad_manana = models.PositiveIntegerField(default=6)
    capacidad_tarde = models.PositiveIntegerField(default=4)
    cupos_habilitados = models.BooleanField(default=True)
    class Meta:
        unique_together = ('fecha', 'parroquia_destino')
        ordering = ['fecha']
    def __str__(self): return f"{self.fecha} | {self.parroquia_destino}"


class Turno(models.Model):
    ESTADOS = [
        ('PENDIENTE', 'PENDIENTE (En Revisión)'),
        ('CONFIRMADO', 'CONFIRMADO (Programado)'),
        ('EJECUTADA', 'EJECUTADA (Pendiente Informe)'), # <--- NUEVO ESTADO
        ('RECHAZADO', 'RECHAZADO (Por Inspector)'),
        ('TERMINADO', 'TERMINADO (Inspección Exitosa)'),
        ('CANCELADO', 'CANCELADO (Por Usuario/Staff)'),
        ('NO_REALIZADA', 'NO REALIZADA (Ausente/Incumplido)'),
    ]
    
    BLOQUES = [
        ('MANANA', 'MAÑANA (09:00 - 12:30)'),
        ('TARDE', 'TARDE (14:45 - 16:30)'),
    ]
    
    agenda = models.ForeignKey(AgendaDiaria, on_delete=models.CASCADE, related_name='turnos')
    establecimiento = models.ForeignKey(Establecimiento, on_delete=models.CASCADE)
    inspector = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    
    bloque = models.CharField(max_length=10, choices=BLOQUES)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')
    
    telefono_contacto = models.CharField(max_length=15, verbose_name="Teléfono de Contacto")
    referencia_ubicacion = models.CharField(max_length=255, verbose_name="Referencia de Ubicación", null=True, blank=True)
    
    # Número de formulario físico (Obligatorio para pasar a TERMINADO)
    numero_formulario = models.CharField(max_length=50, verbose_name="N° Formulario Físico", null=True, blank=True)
    
    hora_estimada = models.TimeField(null=True, blank=True) 
    observaciones = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.establecimiento.nombre_comercial} - {self.estado}"

# ==============================================================================
#                              NOTIFICACIONES (NUEVO)
# ==============================================================================

class Notificacion(models.Model):
    TIPOS = [('INFO', 'Información'), ('SUCCESS', 'Éxito'), ('WARNING', 'Alerta'), ('ERROR', 'Error')]
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notificaciones')
    titulo = models.CharField(max_length=100)
    mensaje = models.TextField()
    tipo = models.CharField(max_length=20, choices=TIPOS, default='INFO')
    leido = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    link = models.CharField(max_length=200, null=True, blank=True)
    class Meta: ordering = ['-fecha_creacion']
    def __str__(self): return f"{self.usuario.username} - {self.titulo}"

class Turno(models.Model):
    ESTADOS = [
        ('PENDIENTE', 'PENDIENTE'),
        ('CONFIRMADO', 'CONFIRMADO'),
        ('RECHAZADO', 'RECHAZADO'),
        ('TERMINADO', 'TERMINADO (Inspección Exitosa)'),
        ('CANCELADO', 'CANCELADO (Por Usuario/Staff)'),
        ('NO_REALIZADA', 'NO REALIZADA (Ausente/Incumplido)'),
    ]
    
    # ... (campos agenda, establecimiento, inspector, bloque igual que antes) ...
    agenda = models.ForeignKey(AgendaDiaria, on_delete=models.CASCADE, related_name='turnos')
    establecimiento = models.ForeignKey(Establecimiento, on_delete=models.CASCADE)
    inspector = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    bloque = models.CharField(max_length=10, choices=[('MANANA', 'MAÑANA'), ('TARDE', 'TARDE')])
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')
    telefono_contacto = models.CharField(max_length=15)
    referencia_ubicacion = models.CharField(max_length=255, null=True, blank=True)
    
    numero_formulario = models.CharField(max_length=50, verbose_name="N° Formulario", null=True, blank=True)
    
    # NUEVO CAMPO
    motivo_cancelacion = models.TextField(verbose_name="Motivo Cancelación", null=True, blank=True)
    
    hora_estimada = models.TimeField(null=True, blank=True) 
    observaciones = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.establecimiento.nombre_comercial} - {self.estado}"
# ==============================================================================
#                        GESTIÓN DOCUMENTAL (NUEVO)
# ==============================================================================

class TasaPago(models.Model):
    tipo = models.OneToOneField(TipoEstablecimiento, on_delete=models.CASCADE, verbose_name="Giro de Negocio")
    descripcion = models.CharField(max_length=255, verbose_name="Detalle", default="Permiso de Funcionamiento Anual")
    valor = models.DecimalField(max_digits=6, decimal_places=2, verbose_name="Valor ($)")
    
    # Ordenamiento Automático
    orden = models.PositiveIntegerField(default=0, help_text="Dejar en 0 para auto-asignar al final")
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['orden', 'tipo__nombre']
        verbose_name = "Tasa de Pago"

    def save(self, *args, **kwargs):
        # 1. AUTOMATIZACIÓN: Si orden es 0 o vacío, asignar el último + 1
        if not self.orden:
            max_orden = TasaPago.objects.aggregate(Max('orden'))['orden__max']
            self.orden = (max_orden or 0) + 1
        
        # 2. COLISIÓN: Si el número ya existe, empujar los demás (Shifting)
        else:
            # Verificar si existe OTRO registro con el mismo orden (excluyendo a sí mismo si es edición)
            qs = TasaPago.objects.filter(orden=self.orden)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            
            if qs.exists():
                # Mover todos los registros siguientes una posición adelante (+1)
                # Ej: Si inserto 3, el 3 viejo se vuelve 4, el 4 se vuelve 5...
                TasaPago.objects.filter(orden__gte=self.orden).update(orden=F('orden') + 1)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"[{self.orden}] {self.tipo.nombre} - ${self.valor}"

class RequisitoLegal(models.Model):
    SECCIONES = [
        ('DOC', '1. Documentación Habilitante'),
        ('PQS', '2. Sistema Contra Incendios (Extintores)'),
        ('SEN', '3. Señalética y Evacuación'),
        ('ELE', '4. Sistema Eléctrico'),
        ('GLP', '5. Manejo de Gas (GLP)'),
        ('GEN', '6. Requisitos Generales'),
    ]
    
    seccion = models.CharField(max_length=3, choices=SECCIONES, default='GEN', verbose_name="Categoría")
    titulo = models.CharField(max_length=200, verbose_name="Ítem")
    contenido = models.TextField(verbose_name="Especificación Técnica")
    es_obligatorio = models.BooleanField(default=True)
    
    # Ordenamiento Automático dentro de su sección
    orden = models.PositiveIntegerField(default=0, verbose_name="N° Orden")

    class Meta:
        ordering = ['seccion', 'orden']
        verbose_name = "Requisito Legal"

    def save(self, *args, **kwargs):
        # Lógica Inteligente por SECCIÓN
        # (El orden 1 de 'Documentación' es distinto al orden 1 de 'Extintores')
        
        if not self.orden:
            # Buscar el máximo SOLO dentro de la misma sección
            max_orden = RequisitoLegal.objects.filter(seccion=self.seccion).aggregate(Max('orden'))['orden__max']
            self.orden = (max_orden or 0) + 1
        
        else:
            # Verificar colisión en la misma sección
            qs = RequisitoLegal.objects.filter(seccion=self.seccion, orden=self.orden)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            
            if qs.exists():
                # Empujar hacia abajo solo los de esta sección
                RequisitoLegal.objects.filter(
                    seccion=self.seccion, 
                    orden__gte=self.orden
                ).update(orden=F('orden') + 1)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"[{self.get_seccion_display()}] #{self.orden} {self.titulo}"