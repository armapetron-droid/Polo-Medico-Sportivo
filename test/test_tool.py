import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# Test 1: Verifica che l'infrastruttura risponda all'Health Check
def test_health_check():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "messaggio": "Il server del laboratorio è operativo."}


# Test 2: Verifica il blocco delle rotte protette senza Token
def test_protected_route_without_token():
    response = client.get("/api/v1/bookings/me")
    assert response.status_code == 401
    # Aggiorniamo l'asserzione per farla combaciare con l'intercettazione nativa di FastAPI
    assert response.json()["detail"] == "Not authenticated"


# Test 3: Flusso di registrazione fallito per validazione password corta
def test_registration_validation_error():
    payload = {
        "email": "utente_invalido@test.it",
        "password": "short",  # Meno di 8 caratteri (viola il vincolo in schemas.py)
        "ruolo": "Paziente"
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 422  # Unprocessable Entity (Errore di validazione Pydantic)