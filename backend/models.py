from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Integer, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

#Classe base da cui tutti i modelli erediteranno
class Base(DeclarativeBase):
    pass

class Utente(Base):
    __tablename__ = "utente"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    ruolo: Mapped[str] = mapped_column(String(50), nullable=False) # 'Paziente', 'Medico', 'Admin'
    #L'utente puo' essere sia un paziente che un medico --> relazioni

    paziente: Mapped[Optional["Paziente"]] = relationship(back_populates="utente")
    medico: Mapped[Optional["Medico"]] = relationship(back_populates="utente")


class Paziente(Base):
    __tablename__ = "paziente"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    utente_id: Mapped[int] = mapped_column(ForeignKey("utente.id"), unique=True, nullable=False)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    cognome: Mapped[str] = mapped_column(String(100), nullable=False)
    codice_fiscale: Mapped[str] = mapped_column(String(16), unique=True, nullable=False)
    telefono: Mapped[str | None] = mapped_column(String(20), nullable=True)

    utente: Mapped["Utente"] = relationship(back_populates="paziente")
    prenotazioni: Mapped[List["Prenotazione"]] = relationship(back_populates="paziente")
    certificati: Mapped[List["CertificatoMedico"]] = relationship(back_populates="paziente", cascade="all, delete-orphan")


class Medico(Base):
    __tablename__ = "medico"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    utente_id: Mapped[int] = mapped_column(ForeignKey("utente.id"), unique=True, nullable=False)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    cognome: Mapped[str] = mapped_column(String(100), nullable=False)
    specializzazione: Mapped[str] = mapped_column(String(150), nullable=False)
    
    utente: Mapped["Utente"] = relationship(back_populates="medico")
    slot_orari: Mapped[List["SlotOrario"]] = relationship(back_populates="medico")



class SlotOrario(Base):
    __tablename__ = "slot_orario"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    medico_id: Mapped[int] = mapped_column(ForeignKey("medico.id"), nullable=False)
    data_ora_inizio: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    data_ora_fine: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    stato: Mapped[str] = mapped_column(String(50), nullable=False, default="Libero")
    
    medico: Mapped["Medico"] = relationship(back_populates="slot_orari")
    #forzatura della relazione 1:1 tramite "uselist"
    prenotazione: Mapped[Optional["Prenotazione"]] = relationship(back_populates="slot", uselist=False)


class Prenotazione(Base):
    __tablename__ = "prenotazione"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    paziente_id: Mapped[int] = mapped_column(ForeignKey("paziente.id"), nullable=False)
    #per impedire una doppia prenotazione dello stesso slot, si impone l'unicità del campo slot_id
    slot_id: Mapped[int] = mapped_column(ForeignKey("slot_orario.id"), unique=True, nullable=False)
    
    data_creazione: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    stato: Mapped[str] = mapped_column(String(50), nullable=False, default="Attiva") # 'Attiva', 'Annullata', 'Completata'
    
    paziente: Mapped["Paziente"] = relationship(back_populates="prenotazioni")
    slot: Mapped["SlotOrario"] = relationship(back_populates="prenotazione")
    referto: Mapped[Optional["Referto"]] = relationship(back_populates="prenotazione", uselist=False)

    ciclo_id: Mapped[int | None] = mapped_column(ForeignKey("ciclo_terapeutico.id"), nullable=True)
    ciclo: Mapped["CicloTerapeutico"] = relationship(back_populates="prenotazioni")
    
    
class Referto(Base):
    __tablename__ = "referto"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    prenotazione_id: Mapped[int] = mapped_column(ForeignKey("prenotazione.id"), unique=True, nullable=False)
    paziente_id: Mapped[int] = mapped_column(ForeignKey("paziente.id"), nullable=False)
    testo_diagnosi: Mapped[str] = mapped_column(Text, nullable=False)
    path_file_pdf: Mapped[str] = mapped_column(String(500), nullable=False)
    data_emissione: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    prenotazione: Mapped["Prenotazione"] = relationship(back_populates="referto")



class CertificatoMedico(Base):
    __tablename__ = "certificato_medico"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    paziente_id: Mapped[int] = mapped_column(ForeignKey("paziente.id"), nullable=False)
    medico_id: Mapped[int] = mapped_column(ForeignKey("medico.id"), nullable=False) 
    
    tipo_sport: Mapped[str] = mapped_column(String(100), nullable=False)
    data_emissione: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    data_scadenza: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    idoneo: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Predisposizione per lo storage fisico del PDF (Sprint 2)
    path_file_pdf: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # Relazioni ORM
    paziente: Mapped["Paziente"] = relationship(back_populates="certificati")
    medico: Mapped["Medico"] = relationship()


class CicloTerapeutico(Base):
    __tablename__ = "ciclo_terapeutico"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    paziente_id: Mapped[int] = mapped_column(ForeignKey("paziente.id"), nullable=False)
    # Il medico che ha prescritto o che segue il ciclo
    medico_id: Mapped[int] = mapped_column(ForeignKey("medico.id"), nullable=False) 
    
    nome_terapia: Mapped[str] = mapped_column(String(150), nullable=False)
    totale_sedute: Mapped[int] = mapped_column(nullable=False)
    
    # Relazione 1 a N con le singole prenotazioni (le "sedute")
    prenotazioni: Mapped[List["Prenotazione"]] = relationship(back_populates="ciclo")    