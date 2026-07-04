// ========================================================================
// CORE.JS - NUCLEO DI RETE E UI GLOBALE
// ========================================================================
const API_BASE_URL = "http://127.0.0.1:8000/api/v1";

async function apiFetch(endpoint, options = {}) {
    const token = localStorage.getItem("token");
    const headers = {
        "Content-Type": "application/json",
        ...options.headers
    };
    
    if (token) {
        headers["Authorization"] = `Bearer ${token}`;
    }

    const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    
    const response = await fetch(`${API_BASE_URL}${cleanEndpoint}`, { ...options, headers });

    // IL GUARDIANO GLOBALE: Se il token è morto, fermiamo tutto.
    if (response.status === 401) {
        console.error("Violazione 401: Token scaduto o non valido. Disconnessione forzata.");
        localStorage.removeItem("token");
        
        // Se abbiamo pagine di login separate,si puo' fare un controllo sull'URL qui, 
        // altrimenti rimandiamo alla pagina di accesso principale.
        mostraAlert("Sessione scaduta. Effettua nuovamente l'accesso.", "error");
        setTimeout(() => {
            window.location.href = "login.html"; 
        }, 1500);
        
        // Lancia un'eccezione per bloccare l'esecuzione del codice JS a valle
        throw new Error("Sessione scaduta");
    }

    return response;
}

// ========================================================================
// UTILITY DI INTERFACCIA (RESILIENZA UI)
// ========================================================================

function setButtonLoading(buttonElement, isLoading, textOriginale = "Invia", textLoading = "Elaborazione...") {
    if (!buttonElement) return;
    
    if (isLoading) {
        buttonElement.disabled = true;
        buttonElement.innerHTML = `<span class="spinner" style="display:inline-block; width:12px; height:12px; border:2px solid #fff; border-top:2px solid transparent; border-radius:50%; animation:spin 1s linear infinite;"></span> ${textLoading}`;
        buttonElement.style.opacity = "0.7";
        buttonElement.style.cursor = "not-allowed";
    } else {
        buttonElement.disabled = false;
        buttonElement.innerHTML = textOriginale;
        buttonElement.style.opacity = "1";
        buttonElement.style.cursor = "pointer";
    }
}

function mostraToast(messaggio, tipo = "success") {
    // Controlla se il container esiste, altrimenti lo crea al volo
    let container = document.getElementById("toast-container");
    if (!container) {
        container = document.createElement("div");
        container.id = "toast-container";
        document.body.appendChild(container);
    }

    const toast = document.createElement("div");
    toast.className = `toast ${tipo}`;
    toast.innerText = messaggio;

    container.appendChild(toast);

    setTimeout(() => toast.classList.add("show"), 10);

    setTimeout(() => {
        toast.classList.remove("show");
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}