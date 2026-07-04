// ========================================================================
// CONTROLLER DASHBOARD PAZIENTE
// ========================================================================
// ========================================================================
// UTILITY DI SISTEMA (UI E LOGOUT)
// ========================================================================
function mostraAlert(messaggio, tipo = "success") {
    const box = document.getElementById("alert-box");
    if (!box) return;
    box.innerText = messaggio;
    box.style.background = tipo === "error" ? "#f8d7da" : "#d4edda";
    box.style.color = tipo === "error" ? "#721c24" : "#155724";
    box.style.padding = "10px";
    box.style.marginBottom = "15px";
    box.style.borderRadius = "4px";
    box.style.display = "block";
    setTimeout(() => box.style.display = "none", 5000);
}

function eseguiLogout() {
    if (!confirm("Vuoi uscire dal tuo profilo paziente?")) return;
    localStorage.removeItem("token");
    localStorage.removeItem("ruolo");
    window.location.replace("login.html");
}


// 1. IL MOTORINO DI AVVIAMENTO
// Questa funzione parte automaticamente appena l'HTML è caricato
document.addEventListener("DOMContentLoaded", () => {
    // Controllo barriera: se non hai il token, vieni cacciato al login
    const token = localStorage.getItem("token");
    if (!token) {
        window.location.replace("login.html");
        return;
    }

    // Esecuzione parallela delle chiamate iniziali
    caricaProfiloPaziente();
    caricaSpecializzazioni();
    caricaMiePrenotazioni();
    caricaCertificati();
});


// ========================================================================
// FUNZIONI GLOBALI DI CARICAMENTO DATI (AGENDA, PROFILO, CERTIFICATI)
// ========================================================================

async function caricaSpecializzazioni() {
    const select = document.getElementById("filtro-specializzazione");
    try {
        // 1. Chiamata di rete
        const response = await apiFetch("/specialties", { method: "GET" });
        if (!response.ok) throw new Error("Errore recupero specializzazioni");
        
        // 2. Estrazione del JSON (Il passaggio che hai saltato)
        const specializzazioni = await response.json(); 
        
        select.innerHTML = '<option value="">Tutte le specializzazioni</option>';
        specializzazioni.forEach(spec => {
            const option = document.createElement("option");
            option.value = spec;
            option.textContent = spec;
            select.appendChild(option);
        });
    } catch (error) {
        console.error("Errore specializzazioni:", error);
    }
}

async function caricaProfiloPaziente() {
    const container = document.getElementById("anagrafica-paziente");
    try {
        // 1. Chiamata di rete
        const response = await apiFetch("/pazienti/me/profilo", { method: "GET" });
        if (!response.ok) throw new Error("Errore profilo");
        
        // 2. Estrazione del JSON
        const utente = await response.json(); 
        
        container.innerHTML = `
            <p><strong>Nome:</strong> ${utente.nome} ${utente.cognome}</p>
            <p><strong>Codice Fiscale:</strong> ${utente.codice_fiscale}</p>
            <p><strong>Email:</strong> ${utente.email}</p>
        `;
    } catch (error) {
        console.error("Errore profilo:", error);
        container.innerHTML = `<p class="error-text" style="color: red;">Impossibile caricare il profilo.</p>`;
    }
}

async function caricaMiePrenotazioni() {
    const container = document.getElementById("le-mie-prenotazioni");
    try {
        // Usa apiFetch (corretta) e passa solo la rotta relativa (senza duplicare api/v1)
        const response = await apiFetch("/bookings/me", { method: "GET" });
        
        if (!response.ok) throw new Error("Impossibile recuperare le prenotazioni dal server.");
        
        const prenotazioni = await response.json();
        
        if (prenotazioni.length === 0) {
            container.innerHTML = "<p>Nessuna prenotazione trovata.</p>";
            return;
        }

        let html = '<ul style="list-style: none; padding: 0;">';
        prenotazioni.forEach(p => {
            if (p.stato !== "Annullata") {
                const dataFormat = new Date(p.slot.data_ora_inizio).toLocaleString('it-IT', {
                    day: '2-digit', month: '2-digit', year: 'numeric',
                    hour: '2-digit', minute: '2-digit'
                });
                
                html += `
                <li style="border: 1px solid #ddd; padding: 15px; margin-bottom: 10px; border-radius: 4px; background: #fff; display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong>${dataFormat}</strong> - ${p.slot.medico.specializzazione} <br>
                        Dr. ${p.slot.medico.cognome} <br>
                        <span style="color: green; font-size: 0.9em; font-weight: bold;">Stato: ${p.stato}</span>
                    </div>
                    <button onclick="cancellaPrenotazione(${p.id}, this)" style="background: #dc3545; color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-size: 0.9em;">Annulla</button>
                </li>`;
            }
        });
        html += '</ul>';
        container.innerHTML = html;
        
    } catch (error) {
        console.error("Errore prenotazioni:", error);
        container.innerHTML = `<p class="error-text" style="color: red;">Impossibile caricare le prenotazioni attive.</p>`;
    }
}

async function caricaCertificati() {
    const container = document.getElementById("contenitore-certificati");
    try {
        // 1. Chiamata di rete pura (senza /api/v1 perché è già in core.js)
        const response = await apiFetch("/pazienti/me/certificati", { method: "GET" });
        
        // 2. Barriera di controllo (se il server risponde 404, 500, ecc.)
        if (!response.ok) throw new Error("Impossibile recuperare lo storico dei certificati.");
        
        // 3. Estrazione del payload JSON
        const certificati = await response.json();
        
        if (certificati.length === 0) {
            container.innerHTML = "<p>Nessun certificato medico presente nel tuo storico.</p>";
            return;
        }

        let html = '<ul style="list-style: none; padding: 0;">';
        certificati.forEach(c => {
            const dataEmissione = new Date(c.data_emissione).toLocaleDateString('it-IT');
            const dataScadenza = new Date(c.data_scadenza).toLocaleDateString('it-IT');
            const statoIdoneita = c.idoneo ? 
                '<span style="color: green; font-weight: bold;">IDONEO</span>' : 
                '<span style="color: red; font-weight: bold;">NON IDONEO</span>';

            html += `
            <li style="border: 1px solid #ddd; padding: 15px; margin-bottom: 10px; border-radius: 4px; display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <strong>${c.tipo_sport.toUpperCase()}</strong> <br>
                    Emesso il: ${dataEmissione} | Scadenza: ${dataScadenza} <br>
                    Esito: ${statoIdoneita}
                </div>
                <button onclick="scaricaPDF(${c.id})" style="background-color: #004085; color: white; border: none; padding: 8px 12px; border-radius: 4px; cursor: pointer;">Scarica PDF</button>
            </li>`;
        });
        html += '</ul>';
        container.innerHTML = html;
        
    } catch (error) {
        console.error("Errore certificati:", error);
        container.innerHTML = `<p class="error-text">Errore nel recupero dello storico referti.</p>`;
    }
}

// 3. GESTIONE DOWNLOAD PDF FISICO
async function scaricaPDF(certificatoId) {
    const token = localStorage.getItem("token");
    try {
        const response = await fetch(`http://127.0.0.1:8000/api/v1/certificati/${certificatoId}/download`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) throw new Error("Referto PDF non trovato o accesso negato.");

        // Trasforma la risposta in un file scaricabile
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `Certificato_${certificatoId}.pdf`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);

    } catch (error) {
        alert(error.message);
    }
}
// ========================================================================
// 4. MOTORE OPERATIVO: RICERCA E PRENOTAZIONE
// ========================================================================

// --- MOTORE DI RICERCA SLOT (Aggiornato per ForceX) ---
async function cercaSlot() {
    const dataTarget = document.getElementById("data-ricerca").value;
    const specTarget = document.getElementById("filtro-specializzazione").value;
    const container = document.getElementById("slot-list");
    
    if (!dataTarget) {
        container.innerHTML = `<p style="color: var(--text-muted);">Imposta una data per visualizzare gli appuntamenti liberi.</p>`;
        return;
    }

    let url = `/slots?date=${dataTarget}`;
    if (specTarget) {
        url += `&specializzazione=${encodeURIComponent(specTarget)}`;
    }

    container.innerHTML = `<p style="color: var(--primary-blue); font-weight: 600;">Ricerca disponibilità in corso...</p>`;

    try {
        const response = await apiFetch(url, { method: "GET" });
        if (!response.ok) throw new Error("Errore durante la comunicazione col server.");
        
        const slots = await response.json();
        
        if (slots.length === 0) {
            container.innerHTML = `
                <div style="padding: 20px; text-align: center; background: #f8f9fa; border-radius: var(--border-radius); color: var(--fx-dark); border: 1px dashed #ccc;">
                    Nessun medico disponibile per i criteri selezionati in questa data.
                </div>`;
            return;
        }

        container.innerHTML = ""; 
        slots.forEach(slot => {
            const inizio = new Date(slot.data_ora_inizio).toLocaleTimeString('it-IT', {hour: '2-digit', minute:'2-digit'});
            const divRow = document.createElement("div");
            
            divRow.className = "booking-card"; // Usa la classe CSS ForceX
            divRow.innerHTML = `
                <div>
                    <strong style="color: var(--fx-black); font-size: 1.1em;">${inizio}</strong> 
                    <span style="color: var(--text-muted); margin-left: 10px;">Dott. ${slot.medico.cognome}</span> 
                    <span class="status-badge status-active" style="margin-left: 10px;">${slot.medico.specializzazione}</span>
                </div>
                <div>
                    <button onclick="prenota(${slot.id}, this)" style="background-color: var(--fx-green);">
                        Prenota Ora
                    </button>
                </div>
            `;
            container.appendChild(divRow);
        });

    } catch (error) {
        container.innerHTML = `<p style="color: var(--danger-red); font-weight: bold;">Impossibile recuperare l'agenda.</p>`;
        console.error(error);
    }
}

// --- MOTORE DI PRENOTAZIONE ---
async function prenota(slotId, btnElement) {
    if (!confirm("Confermi la prenotazione definitiva di questa visita specialistica?")) return;

    try {
        // Disabilita il bottone visivamente
        btnElement.disabled = true;
        btnElement.innerText = "Attendere...";
        btnElement.style.backgroundColor = "var(--text-muted)";

        const response = await apiFetch("/bookings", {
            method: "POST",
            body: JSON.stringify({ slot_id: slotId })
        });

        if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.detail || "Errore di prenotazione");
        }

        alert("Visita prenotata con successo. Si ricordi che sara' possibile effettuare l'annullamento entro 24 ore dalla prenotazione.");
        
        // Aggiorna l'interfaccia
        cercaSlot(); 
        if (typeof caricaMiePrenotazioni === "function") {
            caricaMiePrenotazioni(); 
        }
    } catch (error) {
        alert("Prenotazione visita rifiutata: " + error.message);
        // Riattiva il bottone in caso di errore
        btnElement.disabled = false;
        btnElement.innerText = "Prenota Ora";
        btnElement.style.backgroundColor = "var(--fx-green)";
    }
}

// --- MOTORE DI ANNULLAMENTO PRENOTAZIONE ---
async function cancellaPrenotazione(bookingId, btnElement) {
    // Barriera di conferma chirurgica
    if (!confirm("Sei sicuro di voler annullare questa prenotazione? L'operazione è irreversibile.")) return;
    
    try {
        // Disabilitazione visiva ForceX
        btnElement.disabled = true;
        btnElement.innerText = "Annullamento...";
        btnElement.style.backgroundColor = "var(--text-muted)";

        const response = await apiFetch(`/bookings/${bookingId}/cancel`, {
            method: "PUT"
        });

        if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.detail || "Impossibile annullare la prenotazione.");
        }

        // Feedback nativo coerente con la funzione prenota()
        alert("Operazione completata: Prenotazione annullata."); 
        
        // Aggiornamento cascata dei dati
        caricaMiePrenotazioni();
        
        // Se l'utente stava guardando un'agenda, la riaggiorniamo per fargli vedere lo slot tornato libero
        const campoData = document.getElementById("data-ricerca");
        if (campoData && campoData.value) {
            cercaSlot();
        }
        
    } catch (error) {
        alert("Transazione Rifiutata: " + error.message);
        
        // Ripristino visivo ForceX (Rosso per azione distruttiva)
        btnElement.disabled = false;
        btnElement.innerText = "Annulla";
        btnElement.style.backgroundColor = "var(--danger-red)";
    }
}