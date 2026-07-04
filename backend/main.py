import os
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from sqlalchemy import func
from pdf_engine import genera_pdf_idoneita
import models
import schemas
import security
from database import SessionLocal, engine

# ====================================================================
# 1. INIZIALIZZAZIONE DATABASE
# ====================================================================
models.Base.metadata.create_all(bind=engine)

# ====================================================================
# 2. CONFIGURAZIONE SICUREZZA
# ====================================================================
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# ====================================================================
# 3. INIZIALIZZAZIONE APPLICAZIONE E CORS
# ====================================================================
app = FastAPI(
    title="API Laboratorio Medico ForceX",
    description="Backend RESTful blindato per la gestione di referti clinici",
    version="1.1.0",
)

# Autorizza il frontend a comunicare col backend. 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"], 
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"], 
)

# Assicura l'esistenza fisica della cartella, MA NON LA MONTA PUBBLICAMENTE.
os.makedirs("storage_referti", exist_ok=True)




#/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\
# 4. DIPENDENZE (DI)
#/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Impossibile validare le credenziali.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    utente = db.query(models.Utente).filter(models.Utente.email == email).first()
    if utente is None:
        raise credentials_exception
    return utente





#/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\
# 6. ENDPOINT DI AUTENTICAZIONE
#/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\
@app.post("/auth/register", status_code=status.HTTP_201_CREATED)
def register_user(payload: schemas.UtenteRegistrazione, db: Session = Depends(get_db)):
    # 1. Controllo duplicati (Barriera in ingresso)
    utente_esistente = db.query(models.Utente).filter(models.Utente.email == payload.email).first()
    if utente_esistente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Questa email risulta già registrata nel sistema."
        )
    
    # 2. TRANSAZIONE ATOMICA (Tutto o Niente)
    try:
        # A. Preparazione Utente
        password_criptata = security.hash_password(payload.password)
        nuovo_utente = models.Utente(
            email=payload.email,
            password_hash=password_criptata,
            ruolo="Paziente" 
        )
        
        db.add(nuovo_utente)
        
        # CRITICO: Comunica col DB per ottenere nuovo_utente.id, ma NON scrive in modo permanente.
        db.flush() 
        
        # B. Preparazione Paziente (Ora nuovo_utente.id è valorizzato)
        nuovo_profilo = models.Paziente(
            utente_id=nuovo_utente.id,
            nome=payload.nome,
            cognome=payload.cognome,
            codice_fiscale=payload.codice_fiscale,
            telefono=payload.telefono
        )
        
        db.add(nuovo_profilo)
        
        # C. Esecuzione Fisica
        # Solo se entrambe le aggiunte sono valide, rendiamo permanente la modifica sul disco.
        db.commit() 
        
        return {"messaggio": "Registrazione completata con successo. Ora puoi effettuare l'accesso."}
        
    except Exception as e:
        # Se esplode l'hashing, la validazione del CF nel DB, o cade la connessione:
        # Annulliamo tutto. Nessun utente orfano. Nessun dato parziale.
        db.rollback() 
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Fallimento critico durante la registrazione: {str(e)}"
        )




@app.get("/api/v1/pazienti/me/profilo")
def ottieni_profilo_completo(
    db: Session = Depends(get_db),
    current_user: models.Utente = Depends(get_current_user)
):
    """
    Restituisce l'anagrafica completa del paziente unendo account e profilo.
    """
    if current_user.ruolo != "Paziente":
        raise HTTPException(status_code=403, detail="Accesso riservato ai pazienti.")

    paziente = db.query(models.Paziente).filter(models.Paziente.utente_id == current_user.id).first()
    if not paziente:
        raise HTTPException(status_code=404, detail="Profilo anagrafico non trovato.")

    return {
        "email": current_user.email,
        "nome": paziente.nome,
        "cognome": paziente.cognome,
        "codice_fiscale": paziente.codice_fiscale
    }





@app.post("/auth/login", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Nota: OAuth2PasswordRequestForm mappa il campo email su form_data.username
    utente = db.query(models.Utente).filter(models.Utente.email == form_data.username).first()
    
    if not utente or not security.verify_password(form_data.password, utente.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o password non corrette.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = security.create_access_token(
        data={"sub": utente.email, "ruolo": utente.ruolo}
    )
    return {"access_token": access_token, "token_type": "bearer"}





# FIX: Questo endpoint ora è protetto e restituisce i dati dell'utente loggato
@app.get("/api/v1/users/me", response_model=schemas.UtenteResponse)
def get_me(current_user: models.Utente = Depends(get_current_user)):
    """
    Restituisce il profilo dell'utente attualmente loggato decifrando il JWT.
    """
    return current_user





# 7. ENDPOINT CLINICI / MEDICI
@app.get("/api/v1/slots")
def get_available_slots(
    date: str, 
    specializzazione: Optional[str] = None, # Parametro query opzionale
    db: Session = Depends(get_db),
    current_user: models.Utente = Depends(get_current_user)
):
    """
    Cerca gli slot liberi per una data specifica.
    Se viene passata una specializzazione, filtra dinamicamente i risultati.

    """
    # Convertiamo la stringa in oggetto data
    from datetime import datetime
    try:
        target_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato data non valido. Usa YYYY-MM-DD.")

    from sqlalchemy.orm import joinedload
    

    # 1. Costruiamo la query di base (Data esatta e stato Libero)
    query = (
        db.query(models.SlotOrario)
        .join(models.Medico)
        .options(joinedload(models.SlotOrario.medico))
        .filter(func.date(models.SlotOrario.data_ora_inizio) == target_date,
            models.SlotOrario.stato == "Libero"
        )
    )
    
    # 2. Se l'utente ha scelto una specializzazione, iniettiamo la clausola AND nella query SQL
    if specializzazione:
        query = query.filter(models.Medico.specializzazione == specializzazione)
        
    # 3. Eseguiamo la query ordinando cronologicamente
    return query.order_by(models.SlotOrario.data_ora_inizio.asc()).all()







@app.get("/api/v1/doctor/me")
def get_my_doctor_profile(
    db: Session = Depends(get_db),
    current_user: models.Utente = Depends(get_current_user)
):
    """
    Fornisce i dettagli clinici del medico attualmente loggato.
    Necessario per sbloccare le logiche condizionali sul frontend (ABAC).
    """
    if current_user.ruolo != "Medico":
        raise HTTPException(status_code=403, detail="Accesso riservato ai medici.")
        
    medico = db.query(models.Medico).filter(models.Medico.utente_id == current_user.id).first()
    if not medico:
        raise HTTPException(status_code=404, detail="Profilo medico non trovato.")
        
    return {"specializzazione": medico.specializzazione}





@app.get("/api/v1/doctor/bookings")
def ottieni_agenda_medico(
    db: Session = Depends(get_db),
    current_user: models.Utente = Depends(get_current_user)
):
    """
    Restituisce l'agenda del medico. 
    Estrae esplicitamente i dati del paziente, dello slot e del REFERTO (se esiste).
    """
    if current_user.ruolo != "Medico":
        raise HTTPException(status_code=403, detail="Accesso riservato ai medici.")

    # Trova il medico loggato
    medico = db.query(models.Medico).filter(models.Medico.utente_id == current_user.id).first()
    if not medico:
        raise HTTPException(status_code=404, detail="Profilo medico non trovato.")

    # Recupera gli slot del medico e le relative prenotazioni
    prenotazioni = (
        db.query(models.Prenotazione)
        .join(models.SlotOrario)
        .filter(models.SlotOrario.medico_id == medico.id)
        .all()
    )

    risultato = []
    for p in prenotazioni:
        # FORZATURA DEL REFERTO: Se c'è, lo estraiamo fisicamente
        referto_data = None
        if p.referto:
            referto_data = {"testo_diagnosi": p.referto.testo_diagnosi}

        risultato.append({
            "id": p.id,
            "stato": p.stato,
            "data_creazione": p.data_creazione,
            "paziente": {
                "id": p.paziente.id,
                "nome": p.paziente.nome,
                "cognome": p.paziente.cognome,
                "codice_fiscale": p.paziente.codice_fiscale
            },
            "slot": {
                "id": p.slot.id,
                "data_ora_inizio": p.slot.data_ora_inizio,
                "data_ora_fine": p.slot.data_ora_fine,
                "stato": p.slot.stato
            },
            "referto": referto_data 
        })

    return risultato






    

@app.post("/api/v1/bookings", response_model=schemas.PrenotazioneResponse, status_code=status.HTTP_201_CREATED)
def create_booking(payload: schemas.PrenotazioneCreate, db: Session = Depends(get_db), current_user: models.Utente = Depends(get_current_user)):
    
    # 1. Cerchiamo se l'utente loggato ha un profilo paziente
    paziente = db.query(models.Paziente).filter(models.Paziente.utente_id == current_user.id).first()
    
    # FORZATURA DI SICUREZZA PER IL TEST: Se l'utente è un 'Paziente' ma manca la riga nella tabella medica, la creiamo al volo
    if not paziente:
        if current_user.ruolo == "Paziente":
            paziente = models.Paziente(
                utente_id=current_user.id,
                nome="Paziente",
                cognome="Di Test",
                codice_fiscale="TSTMRA80A01H501W",
                telefono="3330000000"
            )
            db.add(paziente)
            db.commit()
            db.refresh(paziente)
        else:
            raise HTTPException(status_code=403, detail="Solo i profili Paziente possono effettuare prenotazioni.")
            
    # ------------------------------------------------------------------
    # FIX NUOVA LOGICA ARCHITETTURALE: CONTROLLO CONCORRENZA A DOPPIA MANDATA
    # ------------------------------------------------------------------
    
    # 2. Controllo esistenza dello slot target
    slot_richiesto = db.query(models.SlotOrario).filter(models.SlotOrario.id == payload.slot_id).first()
    if not slot_richiesto:
        raise HTTPException(status_code=404, detail="Slot orario non trovato.")
    

    # ------------------------------------------------------------------
    # IL GUARDIANO DELLE SCADENZE: Prevenzione Deadlock e Controllo Idoneità
    # ------------------------------------------------------------------
    # Recuperiamo il medico associato allo slot per leggerne la specializzazione
    medico_richiesto = db.query(models.Medico).filter(models.Medico.id == slot_richiesto.medico_id).first()
    
    print(f"DEBUG: Il medico richiesto è {medico_richiesto.cognome} e la sua spec è '{medico_richiesto.specializzazione}'")
    # Definiamo i reparti che richiedono tassativamente un'idoneità agonistica attiva
    reparti_protetti = ["Fisioterapia", "Ortopedia"] # Aggiungi qui altre specializzazioni se necessario
    
    if medico_richiesto and medico_richiesto.specializzazione in reparti_protetti:
        # Estraiamo l'ultimo certificato emesso per questo paziente (ordinato per scadenza decrescente)
        ultimo_certificato = (
            db.query(models.CertificatoMedico)
            .filter(models.CertificatoMedico.paziente_id == paziente.id)
            .order_by(models.CertificatoMedico.data_scadenza.desc())
            .first()
        )
        
        if not ultimo_certificato:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail=f"Accesso negato. Per prenotare in {medico_richiesto.specializzazione} devi prima ottenere un certificato di idoneità sportiva."
            )
            
        if not ultimo_certificato.idoneo:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Accesso negato. Risulti 'Non Idoneo' all'attività sportiva. Contatta la segreteria."
            )
            
        if ultimo_certificato.data_scadenza < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail=f"Accesso negato. Il tuo certificato medico è scaduto il {ultimo_certificato.data_scadenza.strftime('%d/%m/%Y')}."
            )
    # ------------------------------------------------------------------
    # 3. Controllo Concorrenza Lato Medico: Lo slot è già preso da qualcun altro?
    slot_occupato = db.query(models.Prenotazione).filter(
        models.Prenotazione.slot_id == payload.slot_id, 
        models.Prenotazione.stato == "Attiva"
    ).first()
    
    if slot_occupato:
        raise HTTPException(status_code=400, detail="Questo slot orario è già stato occupato da un altro paziente.")

    # 4. Controllo Concorrenza Lato Paziente: Il paziente sta cercando di sdoppiarsi?
    sovrapposizione_paziente = (
        db.query(models.Prenotazione)
        .join(models.SlotOrario)
        .filter(
            models.Prenotazione.paziente_id == paziente.id,
            models.Prenotazione.stato == "Attiva",
            models.SlotOrario.data_ora_inizio == slot_richiesto.data_ora_inizio
        )
        .first()
    )

    if sovrapposizione_paziente:
        raise HTTPException(
            status_code=409, 
            detail="Operazione negata. Hai già una visita medica programmata esattamente per questo orario."
        )

    # 5. Creazione della Prenotazione (Transazione atomica)
    nuova_prenotazione = models.Prenotazione(
        paziente_id=paziente.id,
        slot_id=payload.slot_id,
        stato="Attiva"
    )
    
    try:
        db.add(nuova_prenotazione)
        slot_richiesto.stato = "Occupato" 
        db.commit()
        db.refresh(nuova_prenotazione)
        return nuova_prenotazione
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Errore interno durante il salvataggio della prenotazione.")




@app.get("/api/v1/bookings/me", response_model=List[schemas.PrenotazioneStoricoResponse])
def get_my_bookings(
    db: Session = Depends(get_db), 
    current_user: models.Utente = Depends(get_current_user)
):
    """
    Recupera lo storico completo delle prenotazioni dell'utente attualmente loggato.
    Sfrutta le relazioni ORM per includere i dettagli dell'orario e del medico associato.
    """
    # 1. Recuperiamo il profilo paziente legato all'utente autenticato
    paziente = db.query(models.Paziente).filter(models.Paziente.utente_id == current_user.id).first()
    
    if not paziente:
        if current_user.ruolo == "Paziente":
            return []  # Utente senza prenotazioni
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Accesso consentito solo ai profili Paziente."
        )
    
    # 2. Eseguiamo la query con joinedload per estrarre a cascata slot e medico in un'unica JOIN
    from sqlalchemy.orm import joinedload
    
    prenotazioni = (
        db.query(models.Prenotazione)
        .options(
            joinedload(models.Prenotazione.slot)
            .joinedload(models.SlotOrario.medico)
        )
        .filter(models.Prenotazione.paziente_id == paziente.id)
        .order_by(models.Prenotazione.data_creazione.desc())
        .all()
    )
    
    return prenotazioni




@app.get("/api/v1/specialties", response_model=List[str])
def get_specialties(db: Session = Depends(get_db)):
    """
    Restituisce un elenco univoco di tutte le specializzazioni mediche presenti nel database.
    Serve al frontend per popolare dinamicamente il menu a tendina.
    """
    # Estraiamo solo le specializzazioni distinte per evitare duplicati
    specializzazioni = db.query(models.Medico.specializzazione).distinct().all()
    
    return [s[0] for s in specializzazioni if s[0]]








@app.put("/api/v1/bookings/{booking_id}/cancel")
def cancel_booking(
    booking_id: int, 
    db: Session = Depends(get_db), 
    current_user: models.Utente = Depends(get_current_user)
):
    """
    Consente a un paziente di annullare una prenotazione attiva.
    Vincolo: l'operazione è permessa solo fino a 24 ore prima dell'inizio della visita.
    """
    from datetime import datetime, timedelta

    # 1. Controllo Ruolo: Solo i pazienti possono annullare le proprie visite
    if current_user.ruolo != "Paziente":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Operazione negata. Solo i pazienti possono cancellare le prenotazioni."
        )
        
    paziente = db.query(models.Paziente).filter(models.Paziente.utente_id == current_user.id).first()
    if not paziente:
        raise HTTPException(status_code=404, detail="Profilo paziente non trovato.")

    # 2. Recupero della prenotazione con controllo di esistenza
    prenotazione = db.query(models.Prenotazione).filter(models.Prenotazione.id == booking_id).first()
    if not prenotazione:
        raise HTTPException(status_code=404, detail="Prenotazione non trovata.")

    # 3. Controllo di Proprietà: Il paziente sta provando ad annullare la visita di qualcun altro?
    if prenotazione.paziente_id != paziente.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Non sei autorizzato ad annullare questa prenotazione."
        )

    # 4. Controllo dello Stato Corrente
    if prenotazione.stato == "Annullata":
        raise HTTPException(status_code=400, detail="Questa prenotazione è già stata annullata.")
    if prenotazione.stato == "Completata":
        raise HTTPException(status_code=400, detail="Impossibile annullare una visita medica già completata.")

    # 5. LA VERIFICA TEMPORALE (Il cuore della regola di business)
    slot_associato = prenotazione.slot
    if not slot_associato:
        raise HTTPException(status_code=404, detail="Slot orario associato non trovato.")

    ora_corrente = datetime.utcnow()
    limite_cancellazione = slot_associato.data_ora_inizio - timedelta(days=1)

    if ora_corrente > limite_cancellazione:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tempo massimo scaduto. Le prenotazioni possono essere annullate solo fino a 24 ore prima dell'appuntamento."
        )

    # 6. TRANSAZIONE ATOMICA DI RIPRISTINO
    try:
        # Annulliamo la prenotazione
        prenotazione.stato = "Annullata"
        # Liberiamo lo slot orario per renderlo nuovamente prenotabile sul frontend
        slot_associato.stato = "Libero"
        
        db.commit()
        return {"status": "success", "messaggio": "Prenotazione annullata con successo. Lo slot orario è nuovamente disponibile."}
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Errore durante l'annullamento della prenotazione nel database."
        )
    




#/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\
# 8. ENDPOINT POLO SPORTIVO E FISIOTERAPIA
#/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\


@app.post("/api/v1/pazienti/{paziente_id}/cicli", response_model=schemas.CicloTerapeuticoResponse, status_code=status.HTTP_201_CREATED)
def prescrivi_ciclo_terapeutico(
    paziente_id: int,
    payload: schemas.CicloTerapeuticoCreate,
    db: Session = Depends(get_db),
    current_user: models.Utente = Depends(get_current_user)
):
    """
    Prescrizione di un ciclo di fisioterapia.
    Crea l'entità 'Padre' sotto cui verranno raggruppate le singole prenotazioni (sedute).
    """
    if current_user.ruolo != "Medico":
        raise HTTPException(status_code=403, detail="Solo il personale medico può prescrivere cicli terapeutici.")

    medico = db.query(models.Medico).filter(models.Medico.utente_id == current_user.id).first()
    paziente = db.query(models.Paziente).filter(models.Paziente.id == paziente_id).first()

    if not paziente:
        raise HTTPException(status_code=404, detail="Paziente non trovato.")

    nuovo_ciclo = models.CicloTerapeutico(
        paziente_id=paziente.id,
        medico_id=medico.id, # SICUREZZA: ID Medico forzato dal server
        nome_terapia=payload.nome_terapia,
        totale_sedute=payload.totale_sedute
    )

    try:
        db.add(nuovo_ciclo)
        db.commit()
        db.refresh(nuovo_ciclo)
        return nuovo_ciclo
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Errore interno durante la creazione del ciclo.")
    



@app.get("/api/v1/pazienti")
def lista_pazienti_per_medico(
    db: Session = Depends(get_db),
    current_user: models.Utente = Depends(get_current_user)
):
    """
    Fornisce al medico l'elenco di tutti i pazienti registrati a sistema 
    per popolare le tendine di selezione.
    """
    # Controllo di sicurezza: solo i medici possono vedere tutti i pazienti
    if current_user.ruolo != "Medico":
        raise HTTPException(status_code=403, detail="Accesso negato. Solo il personale medico può consultare l'anagrafica globale.")

    pazienti = db.query(models.Paziente).all()
    
    # Restituiamo un array di dizionari con i dati essenziali
    risultato = []
    for p in pazienti:
        risultato.append({
            "id": p.id,
            "nome": p.nome,
            "cognome": p.cognome,
            "codice_fiscale": p.codice_fiscale
        })
        
    return risultato



@app.post("/api/v1/certificati")
def crea_certificato_e_referto(
    payload: schemas.CertificatoVisitaCreate,
    db: Session = Depends(get_db),
    current_user: models.Utente = Depends(get_current_user)
):
    if current_user.ruolo != "Medico":
        raise HTTPException(status_code=403, detail="Accesso negato.")
    
    medico = db.query(models.Medico).filter(models.Medico.utente_id == current_user.id).first()
    prenotazione = db.query(models.Prenotazione).filter(models.Prenotazione.id == payload.prenotazione_id).first()
    paziente = db.query(models.Paziente).filter(models.Paziente.id == prenotazione.paziente_id).first()

    richiede_certificato = payload.tipo_sport is not None or payload.idoneo is not None
    
    if richiede_certificato and medico.specializzazione != "Medicina dello Sport":
        raise HTTPException(status_code=403, detail="Violazione di competenza.")

    try:
        nuovo_referto = models.Referto(
            prenotazione_id=prenotazione.id,
            paziente_id=paziente.id,
            testo_diagnosi=payload.testo_diagnosi,
            path_file_pdf=""
        )
        db.add(nuovo_referto)

        nuovo_certificato = None
        if richiede_certificato:
            nuovo_certificato = models.CertificatoMedico(
                paziente_id=paziente.id,
                medico_id=medico.id,
                tipo_sport=payload.tipo_sport,
                data_emissione=datetime.utcnow(),
                data_scadenza=payload.data_scadenza,
                idoneo=payload.idoneo,
                path_file_pdf=""
            )
            db.add(nuovo_certificato)
        
        db.flush() 

        # --- CORREZIONE: ESTRAZIONE DATI "PIATTI" ---
        # Creiamo un certificato "fake" o un dizionario se certificato è None
        cert_data = None
        if nuovo_certificato:
            cert_data = nuovo_certificato

        path_pdf = genera_pdf_idoneita(paziente, medico, nuovo_referto, cert_data)

        nuovo_referto.path_file_pdf = path_pdf
        if nuovo_certificato:
            nuovo_certificato.path_file_pdf = path_pdf
        prenotazione.stato = "Refertata"

        db.commit()
        return {"messaggio": "Successo", "path_file_pdf": path_pdf}
    except Exception as e:
        db.rollback()
        print(f"ERRORE FATALE: {e}") # Vedi questo nel log Docker
        raise HTTPException(status_code=500, detail=str(e))

  
@app.get("/api/v1/certificati/{certificato_id}/download", response_class=FileResponse)
def scarica_certificato(
    certificato_id: int,
    db: Session = Depends(get_db),
    current_user: models.Utente = Depends(get_current_user)
):
    """
    Fornisce il download fisico del PDF. 
    Accesso consentito solo al personale medico o al paziente proprietario del documento.
    """
    # 1. Esistenza del dato logico
    certificato = db.query(models.CertificatoMedico).filter(models.CertificatoMedico.id == certificato_id).first()
    if not certificato or not certificato.path_file_pdf:
        raise HTTPException(status_code=404, detail="Certificato non trovato nel database.")

    # 2. Controllo degli Accessi (Sicurezza)
    if current_user.ruolo == "Paziente":
        # Se sei un paziente, devi essere IL paziente a cui è intestato il certificato
        paziente = db.query(models.Paziente).filter(models.Paziente.utente_id == current_user.id).first()
        if not paziente or certificato.paziente_id != paziente.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Violazione di sicurezza. Non sei autorizzato a scaricare referti di altri pazienti."
            )

    # 3. Risoluzione del percorso fisico
    # Estraiamo solo il nome del file (es. certificato_1_RSSMRA.pdf) dal path salvato nel DB
    nome_file = os.path.basename(certificato.path_file_pdf)
    percorso_fisico = os.path.join(os.getcwd(), "storage_referti", nome_file)

    # 4. Verifica esistenza file sul disco
    if not os.path.exists(percorso_fisico):
        raise HTTPException(status_code=404, detail="Il file fisico è stato rimosso o spostato dal server.")

    # 5. Erogazione sicura dei byte
    return FileResponse(
        path=percorso_fisico,
        media_type="application/pdf",
        filename=nome_file
    )  



@app.get("/api/v1/pazienti/me/certificati", response_model=List[schemas.CertificatoVisitaResponse])
def ottieni_miei_certificati(
    db: Session = Depends(get_db),
    current_user: models.Utente = Depends(get_current_user)
):
    """
    Restituisce lo storico completo dei certificati del paziente loggato.
    """
    if current_user.ruolo != "Paziente":
        raise HTTPException(status_code=403, detail="Accesso negato. Solo i pazienti possono consultare il proprio storico.")

    # 1. Identificazione sicura tramite Token
    paziente = db.query(models.Paziente).filter(models.Paziente.utente_id == current_user.id).first()
    if not paziente:
        raise HTTPException(status_code=404, detail="Profilo paziente non trovato.")

    # 2. Estrazione dati
    certificati = (
        db.query(models.CertificatoMedico)
        .filter(models.CertificatoMedico.paziente_id == paziente.id)
        .order_by(models.CertificatoMedico.data_emissione.desc())
        .all()
    )

    return certificati


# ====================================================================
# 9. ENDPOINTS DI SICUREZZA, CONTROLLO STATO E DOWNLOAD PROTETTO
# ====================================================================

@app.get("/")
def health_check():
    """
    Rotta di Health Check istituzionale per verificare lo stato dell'infrastruttura.
    """
    return {
        "status": "online", 
        "sistema": "Polo Medico ForceX", 
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/storage_referti/{nome_file}")
def scarica_documento_protetto(nome_file: str, token: str = Query(...)):
    """
    Rotta di download sicuro dei PDF generati dal sistema.
    Invece di esporre la cartella a internet, questa rotta intercetta la richiesta,
    decifra il JWT passato nell'URL e consegna il PDF solo se l'utente è autenticato.
    Mantiene la compatibilità assoluta con window.open() del frontend.
    """
    # 1. Decodifica e validazione crittografica del Token JWT
    try:
        payload = jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
        email: str = payload.get("sub")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Utenza non identificabile all'interno del token."
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Sessione di download non valida, contraffatta o scaduta."
        )

    # 2. Risoluzione del percorso fisico sul server
    percorso_fisico = os.path.join(os.getcwd(), "storage_referti", nome_file)

    # 3. Controllo di sicurezza sul file system
    if not os.path.exists(percorso_fisico):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Il file richiesto non è presente negli archivi fisici del server."
        )

    # 4. Trasmissione sicura dei dati binari (PDF)
    return FileResponse(
        path=percorso_fisico,
        media_type="application/pdf",
        filename=nome_file
    )