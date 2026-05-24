# Coliseo OS - Sistema de Gestión de Gimnasio

## Integrantes
- Isidora Gonzalez (usrol, plans)
- Benjamin Gutierrez (clase, reser)
- Richard Olguin (pagos, audit)
- Cristobal Rodriguez (profe, notif)

## Requisitos
- Python 3.8+
- Docker Desktop

## Instalación y Ejecución

1. Clonar el repositorio:
git clone https://github.com/Kuttyxo/arq-sw.git
cd arq-sw

2. Ejecutar el sistema:
run_all_demo.bat

Nota: Si necesitas ver los logs de los servicios para depurar errores, usa run_all.bat en su lugar.

## Credenciales de Prueba

| Perfil | RUT | Contraseña |
|--------|-----|------------|
| Alumno | 12345678-9 | 1234 |
| Administrador | 87654321-k | admin123 |
| Profesor | 11111111-1 | 1234 |

## Servicios SOA

| Servicio | Nombre (5 chars) | Función |
|----------|------------------|---------|
| Usuarios | usrol | Gestión de usuarios y roles |
| Planes | plans | Gestión de planes y suscripciones |
| Pagos | pagos | Registro de pagos y comprobantes |
| Auditoría | audit | Historial de cambios del sistema |
| Profesores | profe | Gestión de profesores y asistencia |
| Notificaciones | notif | Envío de notificaciones |
| Clases | clase | Gestión de clases y cupos |
| Reservas | reser | Reservas de clases |

## Estructura del Proyecto

- arq-sw/
  - clientes/
    - cliente_admin.py
    - cliente_alumno.py
    - cliente_profe.py
  - data/
    - usuarios.json
    - planes.json
    - clases.json
    - reservas.json
    - pagos.json
    - historial.json
    - profesores.json
    - notificaciones.json
  - servicios/
    - soa_service_usrol.py
    - soa_service_plans.py
    - soa_service_pagos.py
    - soa_service_audit.py
    - soa_service_profe.py
    - soa_service_notif.py
    - soa_service_clase.py
    - soa_service_reser.py
  - soa_lib.py
  - run_all.bat
  - run_all_demo.bat
  - README.md

## Funcionalidades por Perfil

Administrador:
- Ver y buscar usuarios
- Ver y modificar planes
- Registrar pagos
- Ver historial de pagos
- Ver auditoría de cambios

Alumno:
- Iniciar sesión
- Ver clases disponibles
- Reservar y cancelar clases
- Ver mis reservas
- Ver mi plan activo (clases restantes)

Profesor:
- Ver clases de hoy
- Ver clases de la semana
- Ver lista de alumnos por clase
