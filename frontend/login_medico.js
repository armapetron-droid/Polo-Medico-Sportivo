// login.js - Gestione autenticazione Atleta/Paziente

// 1. Reindirizzamento automatico se già loggato
document.addEventListener("DOMContentLoaded", () => {
    const token = localStorage.getItem("token");
    const ruolo = localStorage.getItem("ruolo");
    if (token && ruolo === "medico") {
        window.location.href = "dashboard_medico.html";
    }
});

// 2. Motore di Autenticazione
async function gestisciLogin(event) {
    // Impedisce al form di ricaricare la pagina a vuoto
    event.preventDefault(); 

    // Aggancio ai nuovi ID dell'HTML ForceX
    const emailInput = document.getElementById("email").value;
    const passwordInput = document.getElementById("password").value;
    const alertBox = document.getElementById("alert-box");

    // Reset visuale
    alertBox.style.display = "none";

    try {
        // Formattazione dati per OAuth2 (standard FastAPI)
        const params = new URLSearchParams();
        params.append('username', emailInput);
        params.append('password', passwordInput);

        // Chiamata di rete verso il backend
        const response = await fetch("http://127.0.0.1:8000/auth/login", {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded"
            },
            body: params
        });

        if (!response.ok) {
            throw new Error("Credenziali non valide o utente non trovato.");
        }

        const data = await response.json();
        
        // Salvataggio nel portafoglio di sicurezza del browser
        localStorage.setItem("token", data.access_token);
        localStorage.setItem("ruolo", "medico"); // Marcatore di ruolo

        // Ingresso nel cruscotto
        window.location.href = "dashboard_medico.html";

    } catch (error) {
        // Esposizione grafica dell'errore
        alertBox.style.display = "block";
        alertBox.textContent = "Accesso Negato: " + error.message;
        alertBox.style.color = "var(--danger-red)";
        alertBox.style.borderLeft = "4px solid var(--danger-red)";
        alertBox.style.backgroundColor = "#fee2e2";
    }
}
