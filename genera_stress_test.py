import sqlite3
import csv
from datetime import datetime, timedelta
import os

# Puntamento esatto al database nella cartella backend
DB_PATH = os.path.join("backend", "laboratorio.db")
CSV_PATH = "slots_jmeter.csv"
MEDICO_ID = 1

def prepara_test_fisico():
    if not os.path.exists(DB_PATH):
        print(f"ERRORE FATALE: Non trovo il database in {DB_PATH}. Fermati e controlla la cartella.")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT MAX(id) FROM slot_orario")
        start_id = (cursor.fetchone()[0] or 0) + 1
        
        nuovi_slots = []
        base_date = datetime(2026, 9, 1, 9, 0) # Settembre per essere sicuri
        
        for i in range(100):
            current_id = start_id + i
            inizio = base_date + timedelta(minutes=30 * i)
            fine = inizio + timedelta(minutes=30)
            nuovi_slots.append((current_id, MEDICO_ID, inizio.strftime("%Y-%m-%d %H:%M:%S.000000"), fine.strftime("%Y-%m-%d %H:%M:%S.000000"), "Libero"))
            
        cursor.executemany("INSERT INTO slot_orario (id, medico_id, data_ora_inizio, data_ora_fine, stato) VALUES (?, ?, ?, ?, ?)", nuovi_slots)
        conn.commit()
        
        with open(CSV_PATH, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["slot_id"])
            for slot in nuovi_slots: writer.writerow([slot[0]])
                
        print(f"SUCCESSO: 100 slot creati nel DB. File {CSV_PATH} pronto.")
    except Exception as e:
        print(f"ERRORE: {e}")
    finally:
        if 'conn' in locals(): conn.close()

if __name__ == "__main__":
    prepara_test_fisico()