@echo off
title COLISEO OS - Demo (Solo Clientes)

echo ========================================
echo   LEVANTANDO COLISEO OS
echo ========================================
echo.

echo [1/3] Iniciando BUS SOA...
docker run -d -p 5000:5000 jrgiadach/soabus:v1 > nul 2>&1
timeout /t 3 /nobreak > nul
echo        BUS listo.

echo [2/3] Iniciando servicios (en segundo plano)...
start /b py servicios/soa_service_usrol.py > nul 2>&1
start /b py servicios/soa_service_plans.py > nul 2>&1
start /b py servicios/soa_service_pagos.py > nul 2>&1
start /b py servicios/soa_service_audit.py > nul 2>&1
start /b py servicios/soa_service_profe.py > nul 2>&1
start /b py servicios/soa_service_notif.py > nul 2>&1
start /b py servicios/soa_service_clase.py > nul 2>&1
start /b py servicios/soa_service_reser.py > nul 2>&1

timeout /t 5 /nobreak > nul
echo        Servicios listos.

echo [3/3] Abriendo clientes...
start "CLIENTE ADMIN" cmd /k "cd /d C:\Users\Isidora\arq-sw && py clientes/cliente_admin.py"
start "CLIENTE ALUMNO" cmd /k "cd /d C:\Users\Isidora\arq-sw && py clientes/cliente_alumno.py"
start "CLIENTE PROFESOR" cmd /k "cd /d C:\Users\Isidora\arq-sw && py clientes/cliente_profe.py"

echo.
echo ========================================
echo   DEMO LISTA
echo ========================================
echo.
echo Servicios corriendo en segundo plano (sin ventanas)
echo Clientes: 3 ventanas abiertas
echo.
echo Para detener los servicios al terminar:
echo 1. Cierra las ventanas de clientes
echo 2. Ejecuta: docker stop $(docker ps -q)
echo 3. Ejecuta: taskkill /F /IM python.exe
echo.
pause
