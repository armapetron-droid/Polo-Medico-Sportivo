// ========================================================================
// GESTIONE REGISTRAZIONE BLINDATA E TRADUZIONE ERRORI
// ========================================================================

function mostraAlert(messaggio, tipo) {
    const box = document.getElementById("alert-box");
    if (!box) return;
    box.innerText = messaggio;
    box.className = tipo === "error" ? "error-msg" : "success-msg";
    box.style.display = "block";
    
    // Auto-nascondi solo i messaggi di successo. Gli errori devono restare visibili per essere letti.
    if (tipo === "success") {
        setTimeout(() => box.style.display = "none", 5000);
    }
}

// Agganciamo l'evento al form, non al bottone
document.getElementById('form-registrazione').addEventListener('submit', async function(event) {
    // 1. BLOCCO ASSOLUTO DEL REFRESH DELLA PAGINA
    event.preventDefault();

    // 2. Estrazione e pulizia dati (CF in maiuscolo come da standard)
    const payload = {
        nome: document.getElementById("nome").value.trim(),
        cognome: document.getElementById("cognome").value.trim(),
        codice_fiscale: document.getElementById("codice_fiscale").value.trim().toUpperCase(),
        telefono: document.getElementById("telefono").value.trim(),
        email: document.getElementById("email").value.trim(),
        password: document.getElementById("password").value
    };

    // 3. Validazione Frontend Pre-Volo (Evita chiamate API inutili)
    if (payload.codice_fiscale.length !== 16) {
        return mostraAlert("Il codice fiscale deve essere esattamente di 16 caratteri.", "error");
    }
    if (payload.password.length < 8) {
        return mostraAlert("La password deve contenere almeno 8 caratteri.", "error");
    }

    try {
        const response = await fetch(`http://127.0.0.1:8000/auth/register`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        // 4. Gestione Intelligente degli Errori
        if (!response.ok) {
            // Se FastAPI lancia un 422 (Errore di validazione Pydantic), detail è un Array
            if (response.status === 422 && Array.isArray(data.detail)) {
                // Estraiamo il primo errore utile per l'utente
                const campoErrato = data.detail[0].loc[data.detail[0].loc.length - 1];
                const msgErrore = data.detail[0].msg;
                throw new Error(`Errore sul campo '${campoErrato}': ${msgErrore}`);
            }
            
            // Altrimenti (es. 400 Utente già registrato), detail è una stringa
            throw new Error(data.detail || "Errore sconosciuto dal server.");
        }

        // 5. Successo
        mostraAlert(data.messaggio || "Registrazione completata! Reindirizzamento in corso...", "success");
        document.getElementById('form-registrazione').reset();
        
        setTimeout(() => {
            window.location.href = "login.html";
        }, 2000);
        
    } catch (error) {
        mostraAlert(error.message, "error");
    }
});