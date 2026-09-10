# Sistema Gestionale per Polo Sportivo Specialistico ForceX
## Architettura Full-Stack API-First disaccoppiata con Docker

Questo progetto implementa una piattaforma software per la gestione delle prenotazioni e della refertazione clinica all'interno di un centro di Medicina dello Sport. 
Il sistema è strutturato seguendo il paradigma dell'architettura client-server disaccoppiata.

### Aderenza ai Requisiti Tecnologici (OOP & Astrazione)
- **Backend (Python / FastAPI):** Sviluppato secondo l'approccio API-First. 
    Rispetta rigorosamente la programmazione orientata agli oggetti (OOP) tramite l'uso di modelli ORM (**SQLAlchemy**) per la mappatura relazionale del database e 
    classi di validazione dei dati (**Pydantic**) per l'integrità dei payload di rete.

- **Frontend (HTML5 / CSS3 / JavaScript Vanilla):** Un'interfaccia leggera, priva di framework pesanti, che consuma in modo asincrono tramite `fetch` gli endpoint protetti del server.

- **Sicurezza:** Autenticazione stateless basata su token **JWT (JSON Web Tokens)** con crittografia simmetrica delle password tramite algoritmo `bcrypt`.

- **Microservizio di Generazione Documentale:** Motore integrato basato su libreria `fpdf2` per l'emissione dinamica e la firma elettronica simulata dei certificati di idoneità in formato PDF.

---

### Prerequisiti
L'intera suite è containerizzata. L'unico prerequisito software richiesto per l'esecuzione è l'installazione di:
- **Docker** e **Docker Compose**

---

### Guida Rapida all'Esecuzione (Deployment in 1 Click)

**1. Clonare il repository ed entrare nella directory radice:**
```bash
git clone https://github.com/armapetron-droid/Polo-Medico-Sportivo.git
cd Polo-Medico-Sportivo


**2. Avvio dell'infrastruttura (modalita' Build)
Scarica le immagini base, configura la rete e i volumi isolati, compila il database SQLite interno e avvia i container Docker dedicati per backend e frontend

```bash
docker-compose up --build -d


**3. Inizializzazione del seeding (Dati di test):
Per popolare istantaneamente il sistema con anagrafiche di test (medici specialisti e atleti) e generare la matrice degli slot orari, eseguire lo script di seeding all'interno del container backend:

```bash
docker exec -it pw16_backend python seed.py


**4. Avvio ed uso dell'applicazione:
Completato l'avvio e il seeding, l'applicativo è esposto sulla porta HTTP standard (80). È possibile navigare l'interfaccia dai seguenti indirizzi:

Home Page: http://localhost (Permette il routing verso i portali dedicati ad Atleti o Medici).

Area Atleta/Paziente: http://localhost/login.html (Accesso, prenotazione visite, annullamento appuntamenti e download referti PDF).

Area Staff Medico: http://localhost/login_medico.html (Accesso riservato per consultazione agende cliniche ed emissione referti da parte del dottore. Le credenziali non sono registrabili liberamente ma fornite dagli admin).

Documentazione Interattiva API (Swagger UI): http://localhost:8000/docs




Credenziali di Collaudo (Generate da Seed)
Staff Medico:
Medico Cardiologo: ibrahimovic@forcex.it / password: password123
Medico Sportivo: zanetti@forcex.it / password: password123
Medico Ortopedico: dimarco@forcex.it / password: password123
Fisioterapista: baggio@forcex.it / password: password123

Pazienti/Atleti:
Paziente 1: paziente.a@forcex.it / password: password123
Paziente 2: paziente.b@forcex.it / password: password123
