import sqlite3
import csv
import os

DB_PATH = "backend/laboratorio.db"
CSV_PATH = "slots_jmeter.csv"

def ripulisci_ambiente():
    if not os.path.exists(CSV_PATH):
        print(f"ERRORE: Il file {CSV_PATH} non esiste. Non ho una traccia degli ID da rimuovere.")
        return
        
    try:
        # Recupero degli ID generati nel test precedente
        ids_da_cancellare = []
        with open(CSV_PATH, 'r') as f:
            reader = csv.reader(f)
            next(reader)  # Salta l'header "slot_id"
            for row in reader:
                if row:
                    ids_da_cancellare.append(str(row[0]))
                    
        if not ids_da_cancellare:
            print("Nessun ID trovato nel file CSV.")
            return

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Cancellazione mirata solo sugli ID presenti nel CSV
        lista_id_str = ",".join(ids_da_cancellare)
        cursor.execute(f"DELETE FROM slot_orario WHERE id IN ({lista_id_str})")
        
        # Cancella anche le eventuali prenotazioni create da JMeter su quegli slot per non lasciare orfani
        cursor.execute(f"DELETE FROM prenotazione WHERE slot_id IN ({lista_id_str})")
        
        conn.commit()
        print(f"SUCCESSO: Rimossi {cursor.rowcount} record associati al test di carico.")
        
        # Elimina il CSV per lasciare la cartella pulita
        os.remove(CSV_PATH)
        print(f"File {CSV_PATH} eliminato con successo.")
        
    except Exception as e:
        print(f"ERRORE FATALE: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    ripulisci_ambiente()