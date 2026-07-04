from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Per lo sviluppo locale usiamo SQLite
# L'argomento check_same_thread è obbligatorio in SQLite quando usato con framework asincroni come FastAPI.
SQLALCHEMY_DATABASE_URL = "sqlite:///./laboratorio.db"

#Engine comunica con il file del database.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, pool_size=100, max_overflow=50, connect_args={"check_same_thread": False}
)

# SessionLocal generasessioni individuali per ogni richiesta.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)