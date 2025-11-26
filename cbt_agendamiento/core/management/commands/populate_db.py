import random
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.contrib.gis.geos import Point
from django.db import transaction
from faker import Faker
from core.models import (
    Establecimiento, TipoEstablecimiento, AgendaDiaria, 
    Turno, PerfilUsuario, OPCIONES_PARROQUIA,
    TasaPago, RequisitoLegal
)

class Command(BaseCommand):
    help = 'Genera un ecosistema de datos completo para pruebas de estrés (Alta Densidad)'

    def handle(self, *args, **kwargs):
        fake = Faker('es_ES')
        self.stdout.write(self.style.WARNING("⚠️  Iniciando simulación masiva de datos..."))

        with transaction.atomic():
            
            # ==========================================
            # 1. CONFIGURACIÓN (TIPOS, TASAS Y REQUISITOS)
            # ==========================================
            self.stdout.write("1. Configurando catálogos extendidos y normativa...")
            
            # Lista ampliada de giros de negocio para mayor variedad
            datos_tipos = [
                ('FARMACIA', 35.00, 'Venta de medicinas y productos de salud'),
                ('TIENDA DE ABARROTES', 15.00, 'Venta al por menor de alimentos'),
                ('RESTAURANTE', 60.00, 'Preparación y venta de comidas'),
                ('PANADERIA', 45.00, 'Elaboración de productos de harina'),
                ('FERRETERIA', 50.00, 'Materiales de construcción'),
                ('BAZAR Y PAPELERIA', 20.00, 'Artículos escolares y regalos'),
                ('DISCOTECA', 120.00, 'Centro de diversión nocturna (Alto Riesgo)'),
                ('MECANICA AUTOMOTRIZ', 80.00, 'Reparación de vehículos'),
                ('HOTEL', 100.00, 'Servicio de hospedaje'),
                ('INDUSTRIA TEXTIL', 150.00, 'Fábrica de ropa (Riesgo Industrial)'),
                ('GIMNASIO', 70.00, 'Centro de entrenamiento físico'),
                ('PELUQUERIA', 25.00, 'Salón de belleza y estética'),
                ('CIBER CAFÉ', 30.00, 'Alquiler de internet y computadoras'),
                ('LUBRICADORA', 90.00, 'Mantenimiento vehicular y aceites'),
                ('CARPINTERIA', 55.00, 'Taller de madera (Riesgo Medio)'),
                ('CONSULTORIO MEDICO', 40.00, 'Atención de salud privada'),
                ('VETERINARIA', 45.00, 'Atención animal e insumos'),
                ('FLORISTERIA', 25.00, 'Venta de arreglos florales'),
                ('CAFETERIA', 40.00, 'Venta de café y bocadillos'),
                ('HELADERIA', 35.00, 'Venta de helados y postres'),
                ('PIZZERIA', 55.00, 'Elaboración de pizzas (Horno)'),
                ('LICORERIA', 50.00, 'Venta de bebidas alcohólicas'),
                ('LAVADORA DE AUTOS', 60.00, 'Limpieza de vehículos'),
                ('SASTRERIA', 20.00, 'Confección de prendas a medida'),
                ('OPTICA', 45.00, 'Venta de lentes y exámenes'),
                ('ZAPATERIA', 30.00, 'Venta de calzado'),
                ('BOUTIQUE', 40.00, 'Venta de ropa exclusiva'),
                ('GARAJE PUBLICO', 80.00, 'Estacionamiento de vehículos'),
                ('BODEGA DE ALMACENAMIENTO', 100.00, 'Depósito de mercaderías varias'),
                ('CENTRO EDUCATIVO', 120.00, 'Escuela o Colegio (Alto Riesgo)'),
            ]

            objs_tipos = []
            for nombre, valor, desc in datos_tipos:
                tipo, created = TipoEstablecimiento.objects.get_or_create(nombre=nombre)
                objs_tipos.append(tipo)
                TasaPago.objects.update_or_create(
                    tipo=tipo,
                    defaults={
                        'valor': valor,
                        'descripcion': desc,
                        'orden': random.randint(1, 30)
                    }
                )

            # Requisitos Legales (Base normativa)
            requisitos_data = [
                ('DOC', 'Copia de RUC actualizada', 'Documento vigente del SRI.'),
                ('DOC', 'Pago de Predio Urbano', 'Comprobante del año en curso.'),
                ('DOC', 'Copia de Cédula', 'Color y legible del propietario.'),
                ('PQS', 'Extintor PQS 10lbs', 'Recargado, con etiqueta vigente y colocado a 1.50m de altura.'),
                ('PQS', 'Extintor CO2 5lbs', 'Para áreas con equipos electrónicos o cocinas.'),
                ('SEN', 'Señalética de Salida', 'Verde y blanca, fotoluminiscente sobre dinteles.'),
                ('SEN', 'Ruta de Evacuación', 'Despejada y señalizada con flechas direccionales.'),
                ('SEN', 'Señalética de Prohibición', 'Prohibido Fumar / Solo Personal Autorizado.'),
                ('ELE', 'Cableado Protegido', 'Todos los cables deben estar entubados o en canaletas.'),
                ('ELE', 'Tablero Eléctrico', 'Identificado y con tapa de protección (Mandil).'),
                ('ELE', 'Luces de Emergencia', 'Operativas en pasillos y salidas.'),
                ('GLP', 'Manguera de Gas', 'Tipo industrial de alta presión con abrazaderas metálicas.'),
                ('GLP', 'Ubicación de Cilindros', 'En lugar ventilado y asegurados con cadenas.'),
                ('GEN', 'Botiquín de Primeros Auxilios', 'Con insumos básicos vigentes (Alcohol, Gasas, etc).'),
                ('GEN', 'Detectores de Humo', 'Instalados en áreas de riesgo (Cocinas, Bodegas).'),
            ]
            
            for sec, tit, cont in requisitos_data:
                RequisitoLegal.objects.get_or_create(
                    titulo=tit,
                    defaults={'seccion': sec, 'contenido': cont, 'orden': random.randint(1, 20)}
                )

            # ==========================================
            # 2. AGENDA EXTENDIDA (1 AÑO)
            # ==========================================
            self.stdout.write("2. Generando agenda operativa anual (-300 a +60 días)...")
            
            parroquias_codigos = [p[0] for p in OPCIONES_PARROQUIA]
            hoy = date.today()
            agendas_creadas = []

            # Rango ampliado: aprox 10 meses atrás y 2 meses adelante
            for i in range(-300, 61): 
                dia = hoy + timedelta(days=i)
                # Crear agenda para 5 parroquias aleatorias por día para aumentar densidad
                zonas_dia = random.sample(parroquias_codigos, 5)
                
                for zona in zonas_dia:
                    # Variabilidad en la capacidad
                    cap_m = random.choice([6, 8, 10, 12])
                    cap_t = random.choice([4, 6, 8])
                    
                    agenda, _ = AgendaDiaria.objects.get_or_create(
                        fecha=dia,
                        parroquia_destino=zona,
                        defaults={'capacidad_manana': cap_m, 'capacidad_tarde': cap_t, 'cupos_habilitados': True}
                    )
                    agendas_creadas.append(agenda)

            # ==========================================
            # 3. CIUDADANOS Y LOCALES (VOLUMEN ALTO)
            # ==========================================
            CANTIDAD_USUARIOS = 1000  # Escalamiento masivo
            self.stdout.write(f"3. Generando {CANTIDAD_USUARIOS} usuarios y establecimientos (esto tomará tiempo)...")

            motivos_cancelacion = [
                "Cliente solicitó cambio de fecha por viaje", 
                "Vehículo de inspección averiado en ruta", 
                "Emergencia operativa de incendio forestal", 
                "Local cerrado al momento de la visita técnica",
                "Falta de documentación habilitante original",
                "Dirección errónea o no ubicada",
                "Condiciones climáticas adversas impidieron acceso",
                "Propietario no contaba con las llaves del local",
                "Reprogramación por enfermedad del inspector",
                "Solicitud duplicada por error del sistema"
            ]
            
            observaciones_inspeccion = [
                "Cumple con toda la normativa vigente. Aprobado.", 
                "Falta señalética en bodega y baño. Se otorga plazo de 8 días.", 
                "Extintor caducado, requiere recarga inmediata.", 
                "Todo en orden, excelente estado de las instalaciones.",
                "Instalaciones eléctricas requieren mantenimiento urgente (cables expuestos).",
                "No dispone de luces de emergencia en la salida.",
                "Cilindros de gas dentro de la cocina, reubicar al exterior.",
                "Local cambió de dirección sin notificar.",
                "Se realizó capacitación breve sobre uso de extintor.",
                "Permiso aprobado, pendiente pago de tasa."
            ]

            batch_size = 500
            created_count = 0

            for _ in range(CANTIDAD_USUARIOS):
                # Datos Aleatorios
                cedula = str(fake.unique.random_number(digits=10, fix_len=True))
                nombre = fake.first_name().upper()
                apellido = fake.last_name().upper()
                
                # Crear Usuario
                user, created = User.objects.get_or_create(username=cedula)
                if created:
                    user.set_password(cedula)
                    user.first_name = nombre
                    user.last_name = apellido
                    user.email = fake.email()
                    user.save()
                    
                    PerfilUsuario.objects.create(
                        user=user,
                        ruc=f"{cedula}001",
                        telefono=f"09{fake.random_number(digits=8, fix_len=True)}",
                        fecha_ultima_actualizacion=date.today() - timedelta(days=random.randint(0, 365))
                    )

                # Locales (1 a 2 por usuario para no saturar tanto, pero mantener volumen)
                for _ in range(random.randint(1, 2)):
                    # Coordenadas Tulcán (Con mayor dispersión para mapa)
                    lat = 0.8119 + random.uniform(-0.03, 0.03)
                    lon = -77.7173 + random.uniform(-0.03, 0.03)
                    
                    local = Establecimiento.objects.create(
                        propietario=user,
                        razon_social=f"{fake.company()} {fake.company_suffix()}".upper(),
                        nombre_comercial=f"{random.choice(objs_tipos).nombre} {fake.last_name()}".upper(),
                        tipo=random.choice(objs_tipos),
                        direccion=fake.street_address().upper(),
                        parroquia=random.choice(parroquias_codigos),
                        ubicacion=Point(lon, lat, srid=4326),
                        ubicacion_verificada=True
                    )

                    # ==========================================
                    # 4. GENERACIÓN DE HISTORIAL Y TURNOS
                    # ==========================================
                    
                    # A. Historial Pasado (Alta probabilidad para simular años de operación)
                    if agendas_creadas and random.random() > 0.2: # 80% tiene historial
                        # Crear 1 o 2 inspecciones pasadas
                        for _ in range(random.randint(1, 2)):
                            agenda_pasada = random.choice([a for a in agendas_creadas if a.fecha < hoy])
                            estado_pasado = random.choices(
                                ['TERMINADO', 'CANCELADO', 'RECHAZADO', 'NO_REALIZADA'], 
                                weights=[70, 10, 10, 10], k=1
                            )[0]
                            
                            num_form = f"F-{random.randint(10000, 99999)}" if estado_pasado == 'TERMINADO' else None
                            motivo = random.choice(motivos_cancelacion) if estado_pasado == 'CANCELADO' else None
                            nota = random.choice(observaciones_inspeccion) if estado_pasado in ['TERMINADO', 'RECHAZADO'] else None

                            try:
                                Turno.objects.create(
                                    agenda=agenda_pasada,
                                    establecimiento=local,
                                    bloque=random.choice(['MANANA', 'TARDE']),
                                    estado=estado_pasado,
                                    telefono_contacto=user.perfil.telefono,
                                    referencia_ubicacion="HISTÓRICO ANUAL",
                                    numero_formulario=num_form,
                                    motivo_cancelacion=motivo,
                                    observaciones=nota
                                )
                            except: pass

                    # B. Turnos Activos (Hoy/Futuro) - Menor probabilidad
                    if random.random() > 0.85: # 15% tiene trámite activo ahora
                        agenda_futura = random.choice([a for a in agendas_creadas if a.fecha >= hoy])
                        # Mayormente pendientes o confirmados
                        estado_futuro = 'CONFIRMADO' if random.random() > 0.4 else 'PENDIENTE'
                        
                        try:
                            Turno.objects.create(
                                agenda=agenda_futura,
                                establecimiento=local,
                                bloque=random.choice(['MANANA', 'TARDE']),
                                estado=estado_futuro,
                                telefono_contacto=user.perfil.telefono,
                                referencia_ubicacion="SOLICITUD WEB RECIENTE",
                            )
                        except: pass

                created_count += 1
                if created_count % batch_size == 0:
                    self.stdout.write(f"   ... {created_count} usuarios procesados ...")

        self.stdout.write(self.style.SUCCESS(f"✅ SIMULACIÓN MASIVA COMPLETADA: 5,000 Usuarios generados en el sistema."))