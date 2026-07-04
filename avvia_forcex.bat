@echo off
echo Avvio del Polo Medico ForceX in corso...
docker-compose down
docker-compose up -d --build
echo L'applicazione e' pronta. Apri http://localhost:3000 nel tuo browser.
pause