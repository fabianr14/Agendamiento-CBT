from django.urls import path
from . import views

urlpatterns = [
    # ==========================================================================
    #                              PANEL DE COMANDO (STAFF)
    # ==========================================================================
    
    # Dashboard Principal
    path('panel-operativo/', views.dashboard_staff, name='dashboard_staff'),
    
    # Gestión de Turnos (Acciones del Flujo)
    path('turno/<int:turno_id>/<str:accion>/', views.gestionar_turno, name='gestionar_turno'), # Aprobar/Rechazar
    path('turno/finalizar/<int:turno_id>/', views.finalizar_turno, name='finalizar_turno'),    # Cerrar con formulario
    
    # --- RUTA AGREGADA (SOLUCIÓN DEL ERROR) ---
    path('turno/cancelar/<int:turno_id>/', views.cancelar_turno, name='cancelar_turno'),

    # Inteligencia Geoespacial
    path('panel-operativo/hoja-ruta/', views.hoja_ruta, name='hoja_ruta'),

    # ==========================================================================
    #                            HERRAMIENTAS OPERATIVAS
    # ==========================================================================

    # 1. Alta de Contribuyente
    path('panel-operativo/alta/', views.alta_contribuyente, name='alta_contribuyente'),
    
    # 2. Gestión de Agenda
    path('panel-operativo/habilitar-agenda/', views.habilitar_agenda, name='habilitar_agenda'),
    path('panel-operativo/agenda/editar/<int:agenda_id>/', views.editar_agenda_detalle, name='editar_agenda'),

    # 3. Ventanilla
    path('panel-operativo/ventanilla/buscar/', views.buscar_local_presencial, name='buscar_local_presencial'),
    path('panel-operativo/ventanilla/agendar/<int:local_id>/', views.agendar_presencial_detalle, name='agendar_presencial_detalle'),

    # ==========================================================================
    #                          BASE DE DATOS Y CONFIGURACIÓN
    # ==========================================================================

    # 1. Directorio
    path('panel-operativo/directorio/', views.directorio_establecimientos, name='directorio_establecimientos'),
    path('panel-operativo/local/<int:local_id>/', views.detalle_establecimiento, name='detalle_establecimiento'),

    # 2. Informes
    path('panel-operativo/informes/', views.generar_informe_mensual, name='generar_informe_mensual'),
    path('panel-operativo/informes/excel/', views.exportar_excel_mensual, name='exportar_excel_mensual'),

    # 3. Tipos de Establecimiento
    path('panel-operativo/tipos/', views.gestion_tipos, name='gestion_tipos'),
    path('panel-operativo/tipos/editar/<int:tipo_id>/', views.editar_tipo, name='editar_tipo'),
    path('panel-operativo/tipos/eliminar/<int:tipo_id>/', views.eliminar_tipo, name='eliminar_tipo'),

    # 4. Gestión de Usuarios
    path('panel-operativo/usuarios/', views.gestion_usuarios, name='gestion_usuarios'),
    path('panel-operativo/usuarios/nuevo-inspector/', views.crear_inspector, name='crear_inspector'),
    path('panel-operativo/usuarios/detalle/<int:user_id>/', views.detalle_usuario, name='detalle_usuario'),
    path('panel-operativo/usuarios/editar/<int:user_id>/', views.editar_usuario, name='editar_usuario'),
    path('panel-operativo/usuarios/eliminar/<int:user_id>/', views.eliminar_usuario, name='eliminar_usuario'),
    path('panel-operativo/usuarios/rol/<int:user_id>/', views.cambiar_rol, name='cambiar_rol'),

    # 5. Documentación
    path('panel-operativo/documentacion/', views.gestion_documentacion, name='gestion_documentacion'),
    path('panel-operativo/documentacion/eliminar/<str:tipo>/<int:id_obj>/', views.eliminar_documento, name='eliminar_documento'),

    # ==========================================================================
    #                                API INTERNA
    # ==========================================================================
    path('api/buscar-propietario/', views.api_buscar_propietario, name='api_buscar_propietario'),
    path('api/notificaciones/', views.api_mis_notificaciones, name='api_mis_notificaciones'),
    path('api/notificaciones/leer/<int:notificacion_id>/', views.api_marcar_leida, name='api_marcar_leida'),

    # NUEVAS RUTAS MODULARES (STAFF)
    path('panel-operativo/solicitudes/', views.solicitudes_pendientes, name='solicitudes_pendientes'),
    path('panel-operativo/inspecciones/', views.gestion_inspecciones, name='gestion_inspecciones'),
    path('panel-operativo/inspecciones/cancelar/', views.cancelar_inspeccion_staff, name='cancelar_inspeccion_staff'),
    path('panel-operativo/cierre/', views.cierre_inspecciones, name='cierre_inspecciones'),
    path('panel-operativo/estadisticas/', views.estadisticas_globales, name='estadisticas_globales'),

    # ==========================================================================
    #                                PORTAL CIUDADANO
    # ==========================================================================
    path('portal/', views.home_ciudadano, name='home_ciudadano'),
    path('portal/registrar-email/', views.registrar_email, name='registrar_email'),
    path('portal/verificar-ubicacion/<int:local_id>/', views.verificar_ubicacion, name='verificar_ubicacion'),
    path('portal/local/<int:local_id>/', views.detalle_local_ciudadano, name='detalle_local_ciudadano'),
    path('portal/agendar/', views.agendar_turno, name='agendar_turno'),
    path('portal/mi-perfil/', views.mi_perfil, name='mi_perfil'),
    
    # Documentación Pública
    path('portal/docs/tasas/', views.ver_tasas_impuestos, name='ver_tasas_impuestos'),
    path('portal/docs/requisitos/', views.ver_guia_requisitos, name='ver_guia_requisitos'),

    path('api/estadisticas/live/', views.api_estadisticas, name='api_estadisticas'),
    
    path('turno/ausente/<int:turno_id>/', views.reportar_ausencia, name='reportar_ausencia'),

    path('turno/ejecutar/<int:turno_id>/', views.marcar_ejecutada, name='marcar_ejecutada'),
]