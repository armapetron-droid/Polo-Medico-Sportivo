# microservizio dedicato alla generazione dei PDF dei certificati e dei referti clinici.
import os
from datetime import datetime
from fpdf import FPDF

# Estendiamo la classe FPDF iniettando la flessibilità per il dipartimento
class CertificatoLayout(FPDF):
    def __init__(self, dipartimento="Servizi Clinici Specialistici", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dipartimento = dipartimento

    def header(self):
        # Intestazione del Polo Sportivo istituzionale
        self.set_font("helvetica", "B", 18)
        self.cell(0, 10, "POLO MEDICO SPORTIVO ForceX", new_x="LMARGIN", new_y="NEXT", align="C")
        self.set_font("helvetica", "I", 12)
        # Il sottotitolo ora muta in base al contesto clinico reale
        self.cell(0, 10, self.dipartimento, new_x="LMARGIN", new_y="NEXT", align="C")
        self.line(10, 30, 200, 30)
        self.ln(15)

    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.cell(0, 10, f"Documento generato digitalmente - Pagina {self.page_no()}/{{nb}}", align="C")


def genera_pdf_idoneita(paziente, medico, referto, certificato=None) -> str:
    """
    Riceve i dati dal backend, discrimina la presenza del certificato,
    genera il layout corretto e restituisce il percorso relativo del file.
    """
    # Determinazione dinamica del dipartimento per l'header
    dipartimento_attivo = (
        "Dipartimento di Medicina dello Sport" 
        if certificato is not None 
        else f"Ambulatorio di {medico.specializzazione}"
    )

    pdf = CertificatoLayout(dipartimento=dipartimento_attivo)
    pdf.add_page()
    
    # 1. Dati Anagrafici Paziente (Universali)
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 10, "DATI ATLETA / PAZIENTE", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "", 12)
    pdf.cell(0, 8, f"Nome e Cognome: {paziente.nome} {paziente.cognome}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, f"Codice Fiscale: {paziente.codice_fiscale}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    # 2. Sezione Condizionale: Esito Valutazione Agonistica (Solo se il certificato esiste)
    if certificato is not None:
        pdf.set_font("helvetica", "B", 14)
        pdf.cell(0, 10, "ESITO VALUTAZIONE AGONISTICA", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("helvetica", "", 12)
        pdf.cell(0, 8, f"Disciplina Sportiva: {certificato.tipo_sport.upper()}", new_x="LMARGIN", new_y="NEXT")
        
        stato_idoneita = "IDONEO" if certificato.idoneo else "NON IDONEO"
        pdf.set_font("helvetica", "B", 16)
        
        # Colorazione semantica legale
        if certificato.idoneo:
            pdf.set_text_color(0, 150, 0) # Verde
        else:
            pdf.set_text_color(200, 0, 0) # Rosso
            
        pdf.cell(0, 12, f"Giudizio Clinico: {stato_idoneita} alla pratica sportiva", new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(0, 0, 0) # Reset immediato dello stato del colore
        pdf.set_font("helvetica", "", 12)
    else:
        # Se il certificato non c'è, stampiamo un'intestazione per il referto specialistico standard
        pdf.set_font("helvetica", "B", 14)
        pdf.cell(0, 10, "CONSULENZA CLINICA SPECIALISTICA", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

    # 3. Testo del Referto Clinico (Universale)
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 8, "REFERTO MEDICO / DIAGNOSI", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "", 11)
    pdf.multi_cell(0, 6, referto.testo_diagnosi)
    pdf.ln(5)
    
    # 4. Date di Validità (Condizionali)
    if certificato is not None:
        data_em = certificato.data_emissione.strftime("%d/%m/%Y")
        data_sc = certificato.data_scadenza.strftime("%d/%m/%Y")
        pdf.cell(0, 8, f"Data di Emissione: {data_em}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 8, f"Valido fino al: {data_sc}", new_x="LMARGIN", new_y="NEXT")
    else:
        # Per un medico comune, stampiamo solo la data di refertazione corrente
        data_rif = datetime.utcnow().strftime("%d/%m/%Y")
        pdf.cell(0, 8, f"Data Rilevazione Clinica: {data_rif}", new_x="LMARGIN", new_y="NEXT")
    
    pdf.ln(10)

    # 5. Sottoscrizione Dinamica del Medico
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 8, "Il Medico Valutatore:", new_x="LMARGIN", new_y="NEXT", align="R")
    nome_medico = getattr(medico, 'nome', 'N/A')
    cognome_medico = getattr(medico, 'cognome', 'N/A')
    spec_medico = getattr(medico, 'specializzazione', 'Non specificata')
    pdf.set_font("helvetica", "", 12)
    pdf.cell(0, 8, f"Dott. {nome_medico} {cognome_medico}", new_x="LMARGIN", new_y="NEXT", align="R")
    pdf.cell(0, 8, f"Spec. in {spec_medico}", new_x="LMARGIN", new_y="NEXT", align="R")

    # 6. Messa in Sicurezza del File Name
    # Se il certificato è None, non possiamo usare certificato.id. 
    # Usiamo referto.id che è garantito dal flush() preventivo sul DB nel main.py.
    id_documento = f"cert_{certificato.id}" if certificato is not None else f"ref_{referto.id}"
    nome_file = f"documento_{id_documento}_{paziente.codice_fiscale}.pdf"
    
    # Isolamento della directory di storage
    directory_target = os.path.join(os.getcwd(), "storage_referti")
    os.makedirs(directory_target, exist_ok=True) # Previene crash se la cartella è stata rimossa
    
    percorso_assoluto = os.path.join(directory_target, nome_file)
    
    # 7. Generazione del file fisico binario
    pdf.output(percorso_assoluto)
    
    return f"/storage_referti/{nome_file}"