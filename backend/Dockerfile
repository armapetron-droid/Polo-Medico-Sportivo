FROM python:3.10-slim

# Imposta la directory di lavoro dentro il container
WORKDIR /app

# Disabilita la cache di Python e forza la stampa dei log in tempo reale
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Copia il file delle dipendenze
COPY requirements.txt /app/

# Installa le dipendenze
RUN pip install --no-cache-dir -r requirements.txt

# Copia tutto il resto del codice backend
COPY . /app/

# Esponi la porta 8000 verso l'esterno
EXPOSE 8000

# Comando di avvio
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]