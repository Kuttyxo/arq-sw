@echo off
title COLISEO OS - Demo

echo ========================================
echo   LEVANTANDO COLISEO OS
echo ========================================
echo.

echo [1/3] Iniciando BUS SOA...
docker run -d -p 5000:5000 jrgiadach/soabus:v1
timeout /t 3 /nobreak > nul
echo        BUS listo.

echo [2/3] Iniciando servicios...
start "usrol" cmd /k "cd /d C:\Users\NTBK\coliseo-os-cristobal && py servicios/soa_service_usrol.py"
start "plans" cmd /k "cd /d C:\Users\NTBK\coliseo-os-cristobal && py servicios/soa_service_plans.py"
start "pagos" cmd /k "cd /d C:\Users\NTBK\coliseo-os-cristobal && py servicios/soa_service_pagos.py"
start "audit" cmd /k "cd /d C:\Users\NTBK\coliseo-os-cristobal && py servicios/soa_service_audit.py"
start "profe" cmd /k "cd /d C:\Users\NTBK\coliseo-os-cristobal && py servicios/soa_service_profe.py"
start "notif" cmd /k "cd /d C:\Users\NTBK\coliseo-os-cristobal && py servicios/soa_service_notif.py"
start "clase" cmd /k "cd /d C:\Users\NTBK\coliseo-os-cristobal && py servicios/soa_service_clase.py"
start "reser" cmd /k "cd /d C:\Users\NTBK\coliseo-os-cristobal && py servicios/soa_service_reser.py"

timeout /t 8 /nobreak > nul

echo [3/3] Abriendo clientes...
start "CLIENTE ADMIN" cmd /k "cd /d C:\Users\NTBK\coliseo-os-cristobal && py clientes/cliente_admin.py"
start "CLIENTE ALUMNO" cmd /k "cd /d C:\Users\NTBK\coliseo-os-cristobal && py clientes/cliente_alumno.py"
start "CLIENTE PROFESOR" cmd /k "cd /d C:\Users\NTBK\coliseo-os-cristobal && py clientes/cliente_profe.py"

echo.
echo ========================================
echo   DEMO LISTA
echo ========================================
echo.
echo Servicios: 8 ventanas abiertas
echo Clientes: 3 ventanas abiertas
echo.
pause
