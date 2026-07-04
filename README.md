# Sistema Gestionale per Polo Sportivo Specialistico (PW16)
## Architettura Full-Stack API-First disaccoppiata con Docker

Questo progetto implementa una piattaforma software per la gestione delle prenotazioni e della refertazione clinica all'interno di un centro di Medicina dello Sport. Il sistema è strutturato seguendo il paradigma dell'architettura client-server disaccoppiata.

### Aderenza ai Requisiti Tecnologici (OOP & Abstrzione)
- **Backend (Python / FastAPI):** Sviluppato secondo l'approccio API-First. Rispetta rigorosamente la programmazione orientata agli oggetti (OOP) tramite l'uso di modelli ORM (**SQLAlchemy**) per la mappatura relazionale del database e classi di validazione dei dati (**Pydantic**) per l'integrità dei payload di rete.
- **Frontend (HTML5 / CSS3 / JavaScript Vanilla):** Un'interfaccia leggera, priva di framework pesanti, che consuma in modo asincrono tramite `fetch` gli endpoint protetti del server.
- **Sicurezza:** Autenticazione stateless basata su token **JWT (JSON Web Tokens)** con crittografia simmetrica delle password tramite algoritmo `bcrypt`.
- **Microservizio di Generazione Documentale:** Motore integrato basato su libreria `fpdf2` per l'emissione dinamica e la firma elettronica simulata dei certificati di idoneità in formato PDF.

---

### Requisiti Prerequisiti
L'intera suite è containerizzata. L'unico prerequisito software richiesto per l'esecuzione è l'installazione di:
- **Docker** e **Docker Compose**

---

### Guida Rapida all'Esecuzione (Deployment in 1 Click)

1. **Clonare il repository ed entrare nella directory radice:**
   ```bash
   cd PW16

## Avviare l'infrastruttura in modalita' build
questo comando dara' modo di scaricare le immagini, configurera' i volumi isolati, compilera' il database SQLite interno ed avvieraà i server dedicati:
  BASH
    docker-compose up --build -d

## Inizializzazione del seeding (dati di test)
per popolare istantaneamente il sistema con medici specialisti (Dr. Cox, Dr. Hosue), atleti di test e slot orari pronti per il collaudo eseguire i seguenti comandi:
BASH
   docker-compose exec api python seed.py


## Avvio ed uso dell'applicazione
Una volta completato l'avvio, l'applicazione rispondera' ai seguenti indirizzi da browser:

http://localhost:3000/index.html   (La pagina di index permette di identificarsi come Atleta/paziente o altrimenti come medico specialista)

http://localhost:3000/login.html  (pagina di login o in assenza di utenza di registrazione dell'atleta per l'accesso alla prenotazione/annullamento delle visite e per la richiesta del certificato di idoneita')

http://localhost:3000/login_medico.html   (pagina di login dei medici specialisti facenti parte del Polo Medico Sportivo. Le credenziali, in un reale ambiente sanitario, sono state fornite degli admin ai diretti interessati ed e' impossibile effettuare alcuna registrazione come medico)

## Documentazione interattiva API con Swagger UI
http://localhost:8000/docs

## Credenziali di collaudo generat da seed
Medico Cardiologo: ibrahimovic@forcex.it / password: password123
Medico Sportivo: zanetti@forcex.it / password: password123
Medico Ortopedico dimarco@forcex.it / password: password123
Fisioterapista baggio@forcex.it / password: password123

Paziente1: paziente.a@forcex.it / password: password123
Paziente2: paziente.b@forcex.it / password: password123








