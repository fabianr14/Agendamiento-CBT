from datetime import time, datetime, timedelta
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

# --- GENERADOR DE HORARIOS ---
def generar_slots_horarios(fecha_obj):
    """
    Genera los bloques de horarios disponibles para una fecha dada.
    Útil si en el futuro se requiere agendamiento por hora específica.
    """
    dia_semana = fecha_obj.weekday() # 0=Lunes, 6=Domingo
    slots = []

    # Horarios diferenciados (Viernes vs Semana)
    if dia_semana == 4: # VIERNES
        inicio_manana = time(10, 0); fin_manana = time(12, 30)
        inicio_tarde = time(14, 45); fin_tarde = time(15, 30)
    else: # LUNES A JUEVES
        inicio_manana = time(9, 0); fin_manana = time(12, 30)
        inicio_tarde = time(14, 45); fin_tarde = time(16, 30)

    def crear_bloque(inicio, fin):
        actual = datetime.combine(fecha_obj, inicio)
        limite = datetime.combine(fecha_obj, fin)
        bloque = []
        while actual < limite:
            bloque.append(actual.time())
            actual += timedelta(minutes=30)
        return bloque

    slots.extend(crear_bloque(inicio_manana, fin_manana))
    slots.extend(crear_bloque(inicio_tarde, fin_tarde))
    return slots

# --- ENVIAR CORREO HTML (INSTITUCIONAL) ---
def enviar_correo_html(destinatario, asunto, template_data):
    """
    Construye y envía un correo electrónico con diseño HTML.
    Dependiendo de settings.EMAIL_BACKEND:
    - Desarrollo: Imprime en consola.
    - Producción: Envía vía AWS SES.
    """
    if not destinatario:
        return False

    # Plantilla HTML embebida para asegurar portabilidad
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f4f4; padding: 20px; margin: 0; }}
            .container {{ max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }}
            .header {{ background-color: #1a1d20; padding: 25px; text-align: center; border-bottom: 5px solid #d62828; }}
            .header h2 {{ color: #ffffff; margin: 0; font-size: 22px; text-transform: uppercase; letter-spacing: 1px; }}
            .header span {{ color: #d62828; font-size: 12px; font-weight: bold; display: block; margin-top: 5px; }}
            .content {{ padding: 30px; color: #333; line-height: 1.6; font-size: 16px; }}
            .info-box {{ background-color: #f8f9fa; border-left: 4px solid #d62828; padding: 15px; margin: 20px 0; border-radius: 4px; }}
            .info-row {{ margin-bottom: 8px; }}
            .footer {{ background-color: #f4f4f4; padding: 20px; text-align: center; font-size: 12px; color: #6c757d; border-top: 1px solid #e9ecef; }}
            .btn {{ display: inline-block; background-color: #d62828; color: #ffffff !important; padding: 12px 25px; text-decoration: none; border-radius: 50px; font-weight: bold; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>Cuerpo de Bomberos</h2>
                <span>TULCÁN - DIGITAL</span>
            </div>
            
            <div class="content">
                <p>Estimado(a) <strong>{template_data.get('nombre', 'Usuario')}</strong>,</p>
                
                <p style="font-size: 18px; font-weight: 500;">{template_data.get('mensaje_principal', '')}</p>
                
                <div class="info-box">
                    <div class="info-row"><strong>Establecimiento:</strong> {template_data.get('local', '--')}</div>
                    <div class="info-row"><strong>Fecha Programada:</strong> {template_data.get('fecha', '--')}</div>
                    <div class="info-row"><strong>Jornada:</strong> {template_data.get('jornada', '--')}</div>
                    <div class="info-row"><strong>Estado Actual:</strong> <span style="color: {template_data.get('color_estado', 'black')}; font-weight: bold;">{template_data.get('estado', '--')}</span></div>
                </div>
                
                <p style="font-size: 14px; color: #555;">
                    <em>{template_data.get('instrucciones', '')}</em>
                </p>

                <center>
                    <a href="http://localhost:8000/portal/" class="btn">Acceder al Portal</a>
                </center>
            </div>

            <div class="footer">
                <p>Este es un mensaje automático del Sistema de Agendamiento.<br>Por favor no responda a este correo.</p>
                <p>&copy; 2025 Cuerpo de Bomberos de Tulcán. Av. Veintimilla y Tarqui.</p>
            </div>
        </div>
    </body>
    </html>
    """

    try:
        # Construir el mensaje
        msg = EmailMultiAlternatives(
            subject=f"[CBT] {asunto}",
            body=strip_tags(html_content), # Versión texto plano automática
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'sistema@cbt.gob.ec'),
            to=[destinatario]
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        
        # Feedback en consola para depuración
        print(f"✅ [EMAIL] Enviado correctamente a {destinatario}")
        return True
    
    except Exception as e:
        print(f"❌ [EMAIL ERROR] No se pudo enviar a {destinatario}: {e}")
        return False