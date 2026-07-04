from datetime import datetime, timedelta
from typing import Union
import bcrypt
from jose import jwt

# hashing delle password


# Configurazione JWT (In produzione queste variabili vanno in un file .env)
SECRET_KEY = "SUPER_SEGRETO_DEL_LABORATORIO_MEDICO_NON_CONDIVIDERE"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def hash_password(password: str) -> str:
    """Prende una password in chiaro e restituisce l'hash bcrypt diretto."""
    # Converte la stringa in byte, genera il salt, calcola l'hash e lo riconverte in stringa
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    password_criptata = bcrypt.hashpw(password_bytes, salt)
    return password_criptata.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica se la password inserita corrisponde all'hash salvato."""
    plain_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(plain_bytes, hashed_bytes)

def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None) -> str:
    """Genera un token JWT firmato con una scadenza temporale."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
