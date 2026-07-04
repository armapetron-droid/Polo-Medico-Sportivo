from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime
from typing import List, Optional

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# SCHEMI UTENTE     
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class UtenteBase(BaseModel):
    email: EmailStr
    ruolo: str = Field(..., pattern="^(Paziente|Medico|Admin)$")

class UtenteCreate(UtenteBase):
    password: str = Field(..., min_length=8)

class UtenteResponse(UtenteBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# SCHEMI REGISTRAZIONE UTENTE (Blindato)
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class UtenteRegistrazione(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, description="La password deve avere almeno 8 caratteri")
    nome: str = Field(..., min_length=2)
    cognome: str = Field(..., min_length=2)
    codice_fiscale: str = Field(..., min_length=16, max_length=16, pattern="^[A-Z0-9]{16}$", description="Codice fiscale di 16 caratteri alfanumerici")
    telefono: str = Field(..., min_length=5)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# SCHEMI MEDICI E PAZIENTI
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class MedicoInfoResponse(BaseModel):
    id: int
    nome: str
    cognome: str
    specializzazione: str
    model_config = ConfigDict(from_attributes=True)

class PazienteInfoResponse(BaseModel):
    id: int
    nome: str
    cognome: str
    codice_fiscale: str
    model_config = ConfigDict(from_attributes=True)    

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# SCHEMI SLOT ORARI (Spostato in alto per evitare NameError)
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ 
class SlotOrarioResponse(BaseModel):
    id: int
    medico_id: int
    data_ora_inizio: datetime
    data_ora_fine: datetime
    stato: str
    model_config = ConfigDict(from_attributes=True)

class SlotDettaglioResponse(BaseModel):
    id: int
    data_ora_inizio: datetime
    data_ora_fine: datetime
    stato: str
    medico: MedicoInfoResponse  
    model_config = ConfigDict(from_attributes=True)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# SCHEMI PRENOTAZIONI E REFERTI
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~     
class PrenotazioneCreate(BaseModel):
    slot_id: int = Field(..., gt=0)
    ciclo_id: Optional[int] = None 

class RefertoSemplice(BaseModel):
    testo_diagnosi: str
    model_config = ConfigDict(from_attributes=True)

# Classe Fusa (Risolto il problema del duplicato)
class PrenotazioneResponse(BaseModel):
    id: int
    paziente_id: int
    slot_id: int
    data_creazione: datetime
    stato: str
    ciclo_id: Optional[int] = None 
    referto: Optional[RefertoSemplice] = None
    model_config = ConfigDict(from_attributes=True)

class PrenotazioneMedicoResponse(BaseModel):
    id: int
    paziente_id: int
    slot_id: int
    data_creazione: datetime
    stato: str
    paziente: PazienteInfoResponse  
    slot: SlotOrarioResponse        
    model_config = ConfigDict(from_attributes=True)

class PrenotazioneStoricoResponse(BaseModel):
    id: int
    paziente_id: int
    slot_id: int
    data_creazione: datetime
    stato: str
    slot: SlotDettaglioResponse  
    model_config = ConfigDict(from_attributes=True)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# SCHEMI TOKEN
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    ruolo: Optional[str] = None

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# SCHEMI CERTIFICATO/REFERTO UNIFICATO
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class CertificatoVisitaCreate(BaseModel):
    # --- CORE CLINICO (Sempre obbligatorio per chiunque) ---
    prenotazione_id: int = Field(..., gt=0)
    testo_diagnosi: str = Field(..., min_length=10)
    
    # --- ESTENSIONE LEGALE (Solo per il Medico dello Sport) ---
    # Usiamo Optional per permettere valori nulli o mancanti
    tipo_sport: Optional[str] = Field(default=None, min_length=2)
    data_scadenza: Optional[datetime] = None
    idoneo: Optional[bool] = None

class CertificatoVisitaResponse(BaseModel):
    id: int
    paziente_id: int
    medico_id: int
    tipo_sport: str
    data_emissione: datetime
    data_scadenza: datetime
    idoneo: bool
    path_file_pdf: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)
    
class CicloTerapeuticoCreate(BaseModel):
    medico_id: int = Field(..., gt=0)
    nome_terapia: str = Field(..., min_length=3)
    totale_sedute: int = Field(..., gt=0)

class CicloTerapeuticoResponse(BaseModel):
    id: int
    paziente_id: int
    medico_id: int
    nome_terapia: str
    totale_sedute: int
    model_config = ConfigDict(from_attributes=True)