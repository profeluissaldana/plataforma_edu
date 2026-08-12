@echo off
:: %COMPUTERNAME% toma automáticamente el nombre de Windows de la PC que ejecuta el archivo
curl -s -X POST http://192.168.1.100:8000/api/reportar-ip/ -d "equipo=%COMPUTERNAME%"