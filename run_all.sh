#!/bin/bash
echo "Levantando BUS SOA..."
docker run -d -p 5000:5000 jrgiadach/soabus:v1
sleep 3

echo "Levantando servicios..."
python servicios/soa_service_usrol.py &
python servicios/soa_service_plans.py &
python servicios/soa_service_pagos.py &
python servicios/soa_service_audit.py &
python servicios/soa_service_profe.py &
python servicios/soa_service_notif.py &
python servicios/soa_service_clase.py &
python servicios/soa_service_reser.py &

echo "Todos los servicios levantados"
echo "Presiona Ctrl+C para detener"
wait
