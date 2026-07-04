// ============================================================================
// VARIABILE GLOBALE PER TRACCIARE LA VISITA IN CORSO
// ============================================================================
let prenotazioneAttivaPerReferto = null;



// ============================================================================
// 1. MOTORE DI AVVIO MEDICO
// ============================================================================
document.addEventListener("DOMContentLoaded", async () => {
    const token = localStorage.getItem("token");
    const ruolo = localStorage.getItem("ruolo");
    
    // Barriera di sicurezza rigida
    if (!token || ruolo !== "medico") {
        localStorage.removeItem("token");
        localStorage.removeItem("ruolo");
        window.location.replace("login_medico.html");
        return;
    }

    // Estrazione e salvataggio della specializzazione per la logica ABAC
    try {
        const response = await apiFetch("/doctor/me", { method: "GET" });
        if (response.ok) {
            const dataMedico = await response.json();
            // ORA il dato esiste e lo memorizziamo
            localStorage.setItem("specializzazione", dataMedico.specializzazione);
        }
    } catch (error) {
        console.error("Fallimento nel recupero dei parametri operativi del medico.", error);
    }

    caricaAgendaMedico();
});



// ============================================================================
// 2. CARICAMENTO AGENDA CLINICA (Endpoint ripristinato)
// ============================================================================
async function caricaAgendaMedico() {
    const container = document.getElementById("agenda-list");
    container.innerHTML = '<p style="color: var(--primary-blue);">Sincronizzazione agenda in corso...</p>';

    try {
        // L'endpoint esatto del tuo server Python
        const response = await apiFetch("/doctor/bookings", { method: "GET" });
        if (!response.ok) throw new Error("Errore di comunicazione col server.");

        const agenda = await response.json();

        if (agenda.length === 0) {
            container.innerHTML = `<div style="padding: 20px; text-align: center; background: #f8fafc; border-radius: var(--border-radius); border: 1px dashed var(--border-color);">
                Nessun appuntamento programmato per te in questo momento.
            </div>`;
            return;
        }

        container.innerHTML = "";
        agenda.forEach(prenotazione => {
            const dataInizio = new Date(prenotazione.slot.data_ora_inizio).toLocaleString('it-IT', {
                day: '2-digit', month: '2-digit', year: 'numeric',
                hour: '2-digit', minute: '2-digit'
            });

            const p = prenotazione.paziente;
            const nomePaziente = p ? `${p.nome} ${p.cognome}` : "Paziente Sconosciuto";
            
            // Logica di refertazione blindata
            let actionHtml = "";
            if (prenotazione.stato === "Attiva") {
                actionHtml = `<button onclick="apriModaleDiagnosi(${prenotazione.id})" style="background-color: var(--fx-green);">Referta Visita</button>`;
            } else {
                actionHtml = `<span class="status-badge status-completed">[${prenotazione.stato}]</span>`;
            }

            const divCard = document.createElement("div");
            divCard.className = "agenda-item";
            divCard.innerHTML = `
                <div>
                    <strong style="color: var(--fx-black); font-size: 1.1em;">${dataInizio}</strong><br>
                    <span style="color: var(--text-muted);">Paziente: <strong>${nomePaziente}</strong></span><br>
                    <span style="font-size: 0.85em; color: #888;">CF: ${p ? p.codice_fiscale : 'N/A'}</span>
                </div>
                <div>
                    ${actionHtml}
                </div>
            `;
            container.appendChild(divCard);
        });

    } catch (error) {
        console.error(error);
        container.innerHTML = `<p style="color: var(--danger-red); font-weight: bold;">Fallimento connessione al server centrale.</p>`;
    }
}



// ============================================================================
// 3. MOTORE REFERTAZIONE (Intelligenza Condizionale ABAC)
// ============================================================================
function apriModaleDiagnosi(idPrenotazione) {
    prenotazioneAttivaPerReferto = idPrenotazione;
    
    // Legge l'identità clinica dalla memoria del browser
    const specializzazione = localStorage.getItem("specializzazione");
    
    // Individua i contenitori (div) dei campi legali
    const campoSport = document.getElementById("cert-sport-modale").parentElement;
    const campoIdoneo = document.getElementById("cert-idoneo-modale").parentElement;
    const campoScadenza = document.getElementById("cert-scadenza-modale").parentElement;
    
    // Reset base della diagnosi (comune a tutti)
    document.getElementById("testo-diagnosi-modale").value = "";
    
    // Diramazione dell'interfaccia
    if (specializzazione === "Medicina dello Sport") {
        // Accende i campi dell'idoneità
        campoSport.style.display = "block";
        campoIdoneo.style.display = "block";
        campoScadenza.style.display = "block";
        
        document.getElementById("cert-sport-modale").value = "";
        document.getElementById("cert-idoneo-modale").value = "true";
        
        const oggi = new Date();
        oggi.setFullYear(oggi.getFullYear() + 1);
        document.getElementById("cert-scadenza-modale").value = oggi.toISOString().split('T')[0];
    } else {
        // Spegne i campi legali per gli specialisti non sportivi (es. Cardiologo)
        campoSport.style.display = "none";
        campoIdoneo.style.display = "none";
        campoScadenza.style.display = "none";
        
        // Pulisce i valori nascosti per non inviare spazzatura
        document.getElementById("cert-sport-modale").value = "";
        document.getElementById("cert-scadenza-modale").value = "";
    }

    document.getElementById("modale-diagnosi").style.display = "flex";
}

function chiudiModaleDiagnosi() {
    document.getElementById("modale-diagnosi").style.display = "none";
    prenotazioneAttivaPerReferto = null;
}

async function salvaDiagnosiDaModale(event) {
    event.preventDefault();

    if (!prenotazioneAttivaPerReferto) return;

    const specializzazione = localStorage.getItem("specializzazione");
    const diagnosiTesto = document.getElementById("testo-diagnosi-modale").value;

    const btnSubmit = event.target.querySelector('button[type="submit"]');
    btnSubmit.disabled = true;
    btnSubmit.innerText = "Elaborazione dati in corso...";

    try {
        // 1. PAYLOAD CLINICO DI BASE (Sempre valido)
        let payload = {
            prenotazione_id: prenotazioneAttivaPerReferto,
            testo_diagnosi: diagnosiTesto
        };

        // 2. PAYLOAD LEGALE ESTESO (Solo per chi ne ha l'autorità)
        if (specializzazione === "Medicina dello Sport") {
            const sport = document.getElementById("cert-sport-modale").value;
            const idoneo = document.getElementById("cert-idoneo-modale").value === "true";
            const scadenza = document.getElementById("cert-scadenza-modale").value;

            // Barriera di validazione frontend
            if (!sport) throw new Error("Il campo sport è obbligatorio per l'idoneità agonistica.");
            if (!scadenza) throw new Error("La data di scadenza del certificato è obbligatoria.");

            payload.tipo_sport = sport;
            payload.idoneo = idoneo;
            payload.data_scadenza = scadenza + "T00:00:00";
        }

        // 3. Trasmissione al Router FastAPI
        const response = await apiFetch("/certificati", {
            method: "POST",
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.detail || "Impossibile generare il referto.");
        }

        const dataCertificato = await response.json();
        alert("Transazione completata con successo.");
        
        // Estrazione e visualizzazione del PDF
        if (dataCertificato.path_file_pdf) {
            const token = localStorage.getItem("token");
            // Usa rigorosamente 127.0.0.1 come l'API base. MAI mischiare le origini!
            const urlCompleto = `http://127.0.0.1:8000${dataCertificato.path_file_pdf}?token=${token}`;
            window.open(urlCompleto, "_blank");
        }

        chiudiModaleDiagnosi();
        caricaAgendaMedico();
        
    } catch (error) {
        alert("Operazione Rifiutata: " + error.message);
    } finally {
        btnSubmit.disabled = false;
        btnSubmit.innerText = "💾 Firma ed Emetti Documento";
    }
}


// ============================================================================
// 4. UTILITY (Logout)
// ============================================================================
function eseguiLogout() {
    if (!confirm("Vuoi disconnetterti in modo sicuro dal portale?")) return;
    localStorage.removeItem("token");
    localStorage.removeItem("ruolo");
    window.location.replace("login_medico.html");
}