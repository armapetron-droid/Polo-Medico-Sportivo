from sqlalchemy.orm import Session
from datetime import datetime, timedelta

# Importa i moduli del tuo progetto
import models
import security  
from database import engine, SessionLocal

def azzera_e_popola():
    print("🚨 INIZIO PROCEDURA DI SEEDING...")
    
    # 1. DISTRUZIONE TOTALE
    print("-> Distruzione tabelle esistenti...")
    models.Base.metadata.drop_all(bind=engine)
    
    # 2. RICOSTRUZIONE
    print("-> Creazione nuove tabelle...")
    models.Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()

    try:
        # Generiamo l'hash della password di test
        password_universale_hash = security.hash_password("password123")

        # ==========================================
        # CREAZIONE UTENTI BASE
        # ==========================================
        print("-> Creazione account di accesso...")
        
        # Array di medici per testare i filtri
        utenti_medici = [
            models.Utente(email="zanetti@forcex.it", password_hash=password_universale_hash, ruolo="Medico"),
            models.Utente(email="ibrahimovic@forcex.it", password_hash=password_universale_hash, ruolo="Medico"),
            models.Utente(email="dimarco@forcex.it", password_hash=password_universale_hash, ruolo="Medico"),
            models.Utente(email="baggio@forcex.it", password_hash=password_universale_hash, ruolo="Medico")
        ]
        
        utente_paz_a = models.Utente(email="paziente.a@forcex.it", password_hash=password_universale_hash, ruolo="Paziente")
        utente_paz_b = models.Utente(email="paziente.b@forcex.it", password_hash=password_universale_hash, ruolo="Paziente")
        
        db.add_all(utenti_medici + [utente_paz_a, utente_paz_b])
        db.commit()

        # ==========================================
        # CREAZIONE PROFILI (Anagrafiche)
        # ==========================================
        print("-> Creazione profili anagrafici...")
        
        medici = [
            models.Medico(utente_id=utenti_medici[0].id, nome="Javier", cognome="Zanetti", specializzazione="Medicina dello Sport"),
            models.Medico(utente_id=utenti_medici[1].id, nome="Roberto", cognome="Baggio", specializzazione="Fisioterapia"),
            models.Medico(utente_id=utenti_medici[2].id, nome="Zlatan", cognome="Ibrahimovic", specializzazione="Cardiologia"),
            models.Medico(utente_id=utenti_medici[3].id, nome="Federico", cognome="Di marco", specializzazione="Ortopedia")
        ]
        
        paziente_a = models.Paziente(utente_id=utente_paz_a.id, nome="Antonio", cognome="Matarrese", codice_fiscale="NTNMTR45A01H501A")
        paziente_b = models.Paziente(utente_id=utente_paz_b.id, nome="Tullio", cognome="De Piscopo", codice_fiscale="TLLDPC65B41H501B")
        
        
        db.add_all(medici + [paziente_a, paziente_b])
        db.commit()

        # ==========================================
        # CREAZIONE SLOT ORARI DINAMICI E PRENOTAZIONI
        # ==========================================
        print("-> Generazione agenda clinica a matrice (prossimi 30 giorni)...")
        ora_attuale = datetime.now()
        
        # 1. Creiamo gli slot specifici per mantenere in piedi le tue prenotazioni di test
        slot_storico = models.SlotOrario(
            medico_id=medici[0].id, 
            data_ora_inizio=ora_attuale - timedelta(days=1), 
            data_ora_fine=ora_attuale - timedelta(days=1) + timedelta(minutes=30),
            stato="Occupato"
        )
        slot_futuro_occ = models.SlotOrario(
            medico_id=medici[0].id, 
            data_ora_inizio=ora_attuale + timedelta(days=1), 
            data_ora_fine=ora_attuale + timedelta(days=1) + timedelta(minutes=30),
            stato="Occupato"
        )
        db.add_all([slot_storico, slot_futuro_occ])
        db.commit()

        # 2. Generazione massiva e algoritmica degli slot liberi per tutti i medici
        for medico in medici:
            for giorni_avanti in range(1, 31):
                data_target = ora_attuale + timedelta(days=giorni_avanti)
                
                # Salta il weekend
                if data_target.weekday() >= 5: 
                    continue
                
                # Turni: 09:00, 10:00, 11:00, 14:00, 15:00, 16:00
                for ora in [9, 10, 11, 14, 15, 16]:
                    inizio_slot = data_target.replace(hour=ora, minute=0, second=0, microsecond=0)
                    
                    # Evitiamo di sovrascrivere lo slot già occupato dal paziente B per House
                    if medico.id == medici[0].id and inizio_slot.date() == slot_futuro_occ.data_ora_inizio.date() and inizio_slot.hour == slot_futuro_occ.data_ora_inizio.hour:
                        continue
                        
                    fine_slot = inizio_slot + timedelta(minutes=30)
                    nuovo_slot = models.SlotOrario(
                        medico_id=medico.id,
                        data_ora_inizio=inizio_slot,
                        data_ora_fine=fine_slot,
                        stato="Libero"
                    )
                    db.add(nuovo_slot)
                    
        db.commit()

        # ==========================================
        # ASSEGNAZIONE PRENOTAZIONI DI TEST
        # ==========================================
        print("-> Assegnazione prenotazioni e storicità...")
        prenotazione_completata = models.Prenotazione(
            paziente_id=paziente_a.id, 
            slot_id=slot_storico.id, 
            stato="Completata"
        )
        prenotazione_attiva = models.Prenotazione(
            paziente_id=paziente_b.id, 
            slot_id=slot_futuro_occ.id, 
            stato="Attiva"
        )
        
        db.add_all([prenotazione_completata, prenotazione_attiva])
        db.commit()

        # ==========================================
        # CREAZIONE REFERTO E CERTIFICATO
        # ==========================================
        print("-> Scrittura referti medici...")
        referto_a = models.Referto(
            prenotazione_id=prenotazione_completata.id, 
            paziente_id=paziente_a.id, 
            testo_diagnosi="Il paziente risulta in perfetta salute. Nessuna anomalia cardiaca rilevata sotto sforzo.",
            path_file_pdf="/fake/path/certificato_1.pdf",
            data_emissione=ora_attuale
        )
        
        certificato_a = models.CertificatoMedico(
            paziente_id=paziente_a.id,
            medico_id=medici[0].id,
            tipo_sport="Calcio Agonistico",
            data_emissione=ora_attuale - timedelta(days=1),
            data_scadenza=ora_attuale + timedelta(days=364),
            idoneo=True,
            path_file_pdf="/fake/path/certificato_1.pdf"
        )
        
        db.add_all([referto_a, certificato_a])
        db.commit()
        
        print("✅ DATABASE POPOLATO CON SUCCESSO. Ambiente di test realistico e pronto.")

    except Exception as e:
        print(f"❌ ERRORE CRITICO DURANTE IL SEEDING: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    azzera_e_popola()