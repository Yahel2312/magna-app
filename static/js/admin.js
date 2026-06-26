// ── Claves de localStorage ────────────────────────────
const TOKEN_KEY  = "magna_admin_token";
const NOMBRE_KEY = "magna_admin_nombre";

// ── Inicialización ────────────────────────────────────
document.addEventListener("DOMContentLoaded", async () => {
    const token = localStorage.getItem(TOKEN_KEY);
    if (token) {
        _mostrarDashboard();
        await cargarDatos();
    } else {
        _mostrarLogin();
    }
});

// ── Login / Logout ─────────────────────────────────────
async function login() {
    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value;
    const errEl    = document.getElementById("login-error");
    errEl.textContent = "";

    if (!username || !password) {
        errEl.textContent = "Ingresa usuario y contraseña.";
        return;
    }

    try {
        const res = await fetch("/auth/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password }),
        });

        if (!res.ok) {
            errEl.textContent = "Usuario o contraseña incorrectos.";
            return;
        }

        const data = await res.json();
        localStorage.setItem(TOKEN_KEY, data.access_token);
        localStorage.setItem(NOMBRE_KEY, data.admin_nombre);
        _mostrarDashboard();
        await cargarDatos();
    } catch (e) {
        errEl.textContent = "Error de conexión.";
    }
}

// Permitir Enter en los campos de login
document.addEventListener("DOMContentLoaded", () => {
    ["username", "password"].forEach(id => {
        document.getElementById(id)?.addEventListener("keydown", e => {
            if (e.key === "Enter") login();
        });
    });
});

function logout() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(NOMBRE_KEY);
    _mostrarLogin();
}

// ── Helpers de visibilidad ─────────────────────────────
function _mostrarLogin() {
    document.getElementById("login-overlay").style.display = "flex";
    document.getElementById("dashboard").style.display = "none";
}

function _mostrarDashboard() {
    document.getElementById("login-overlay").style.display = "none";
    document.getElementById("dashboard").style.display = "flex";
    const nombre = localStorage.getItem(NOMBRE_KEY) || "Admin";
    document.getElementById("admin-nombre").textContent = nombre;
}

function _authHeaders() {
    return { Authorization: `Bearer ${localStorage.getItem(TOKEN_KEY)}` };
}

// ── Carga de datos ─────────────────────────────────────
async function cargarDatos() {
    try {
        const [dashRes, histRes, adminsRes] = await Promise.all([
            fetch("/admin/dashboard",                  { headers: _authHeaders() }),
            fetch("/admin/dashboard/historial?semanas=8", { headers: _authHeaders() }),
            fetch("/admin/admins",                     { headers: _authHeaders() }),
        ]);

        if (dashRes.status === 401 || histRes.status === 401 || adminsRes.status === 401) {
            logout();
            return;
        }

        const dash      = await dashRes.json();
        const historial = await histRes.json();
        const admins    = await adminsRes.json();

        renderStats(dash);
        renderTopRachas(dash.top_rachas);
        renderHistorial(historial);
        renderAdmins(admins);
    } catch (e) {
        console.error("Error cargando datos:", e);
    }
}

// ── Render: tarjetas de stats ─────────────────────────
function renderStats(dash) {
    document.getElementById("stat-total").textContent          = dash.total_asistentes;
    document.getElementById("stat-secundarios").textContent    = dash.por_grupo.Secundarios    ?? 0;
    document.getElementById("stat-prepos").textContent        = dash.por_grupo.Prepos         ?? 0;
    document.getElementById("stat-universitarios").textContent = dash.por_grupo.Universitarios ?? 0;
    document.getElementById("stat-profesionistas").textContent = dash.por_grupo.Profesionistas ?? 0;
    document.getElementById("fecha-evento").textContent        = dash.fecha;
}

// ── Render: top rachas ────────────────────────────────
function renderTopRachas(top) {
    const tbody = document.getElementById("top-rachas-body");
    if (!top || top.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" class="loading">Sin datos aún</td></tr>`;
        return;
    }

    const medals = ["🥇", "🥈", "🥉"];
    tbody.innerHTML = top.map((j, i) => {
        const pos    = medals[i] ?? `${i + 1}.`;
        const badge  = `<span class="badge badge-${j.grupo.toLowerCase()}">${j.grupo}</span>`;
        return `
            <tr>
                <td>${pos}</td>
                <td><strong>${j.nombre}</strong></td>
                <td>${badge}</td>
                <td class="racha-num">🔥 ${j.racha_actual}</td>
                <td style="color:var(--muted)">${j.racha_maxima}</td>
                <td style="color:var(--muted)">${j.puntos_totales}</td>
            </tr>`;
    }).join("");
}

// ── Render: historial semanal ─────────────────────────
let historialChart = null;

function renderHistorial(historial) {
    // Tabla
    const tbody = document.getElementById("historial-body");
    if (!historial || historial.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" class="loading">Sin historial aún</td></tr>`;
        return;
    }

    tbody.innerHTML = historial.map(s => `
        <tr>
            <td>${s.fecha}</td>
            <td><strong>${s.total}</strong></td>
            <td style="color:#93c5fd">${s.por_grupo.Secundarios    ?? 0}</td>
            <td style="color:#d8b4fe">${s.por_grupo.Prepos         ?? 0}</td>
            <td style="color:#5eead4">${s.por_grupo.Universitarios ?? 0}</td>
            <td style="color:#fdba74">${s.por_grupo.Profesionistas ?? 0}</td>
        </tr>`).join("");

    // Chart
    const ctx     = document.getElementById("historial-chart").getContext("2d");
    const reversed = [...historial].reverse();
    const labels  = reversed.map(s => s.fecha);

    if (historialChart) historialChart.destroy();

    historialChart = new Chart(ctx, {
        type: "bar",
        data: {
            labels,
            datasets: [
                {
                    label: "Secundarios",
                    data: reversed.map(s => s.por_grupo.Secundarios ?? 0),
                    backgroundColor: "rgba(59,130,246,0.75)",
                    borderRadius: 4,
                },
                {
                    label: "Prepos",
                    data: reversed.map(s => s.por_grupo.Prepos ?? 0),
                    backgroundColor: "rgba(168,85,247,0.75)",
                    borderRadius: 4,
                },
                {
                    label: "Universitarios",
                    data: reversed.map(s => s.por_grupo.Universitarios ?? 0),
                    backgroundColor: "rgba(20,184,166,0.75)",
                    borderRadius: 4,
                },
                {
                    label: "Profesionistas",
                    data: reversed.map(s => s.por_grupo.Profesionistas ?? 0),
                    backgroundColor: "rgba(249,115,22,0.75)",
                    borderRadius: 4,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { labels: { color: "rgba(255,255,255,0.8)", font: { size: 12 } } },
                tooltip: { mode: "index", intersect: false },
            },
            scales: {
                x: {
                    stacked: true,
                    ticks:   { color: "rgba(255,255,255,0.6)" },
                    grid:    { color: "rgba(255,255,255,0.06)" },
                },
                y: {
                    stacked: true,
                    beginAtZero: true,
                    ticks:   { color: "rgba(255,255,255,0.6)", stepSize: 1 },
                    grid:    { color: "rgba(255,255,255,0.06)" },
                },
            },
        },
    });
}

// ── Descarga de Excel ─────────────────────────────────
async function descargarExcel() {
    try {
        const res = await fetch("/admin/excel/activo", { headers: _authHeaders() });
        if (!res.ok) {
            alert("Error al generar el Excel. Intenta de nuevo.");
            return;
        }
        const blob     = await res.blob();
        const url      = URL.createObjectURL(blob);
        const a        = document.createElement("a");
        a.href         = url;
        a.download     = `asistencia_${new Date().toISOString().slice(0,10)}.xlsx`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    } catch (e) {
        alert("Error de conexión al descargar.");
        console.error(e);
    }
}

// ── Gestión de Admins ──────────────────────────────────

/** Renderiza la tabla de administradores. */
function renderAdmins(admins) {
    const tbody = document.getElementById("admins-body");
    const miUsername = _getMiUsername();

    if (!admins || admins.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" class="loading">Sin administradores</td></tr>`;
        return;
    }

    tbody.innerHTML = admins.map((a, i) => {
        const estadoBadge = a.activo
            ? `<span class="badge badge-activo">Activo</span>`
            : `<span class="badge badge-inactivo">Inactivo</span>`;

        const esYo = a.username === miUsername;
        const btnDesactivar = a.activo
            ? `<button class="btn-deactivate" onclick="desactivarAdmin(${a.id})" ${esYo ? "disabled title=\"No puedes desactivarte a ti mismo\"" : ""}>Desactivar</button>`
            : `<span style="color:var(--muted);font-size:12px">—</span>`;

        return `
            <tr>
                <td style="color:var(--muted)">${i + 1}</td>
                <td><strong>${a.nombre}</strong></td>
                <td style="color:var(--muted);font-family:monospace">${a.username}</td>
                <td>${estadoBadge}</td>
                <td>${btnDesactivar}</td>
            </tr>`;
    }).join("");
}

/** Obtiene el username del admin logueado desde el JWT almacenado. */
function _getMiUsername() {
    try {
        const token = localStorage.getItem(TOKEN_KEY);
        if (!token) return null;
        const payload = JSON.parse(atob(token.split(".")[1]));
        return payload.sub ?? null;
    } catch { return null; }
}

/** Abre el modal de creación de admin. */
function abrirModalAdmin() {
    document.getElementById("new-admin-nombre").value   = "";
    document.getElementById("new-admin-username").value = "";
    document.getElementById("new-admin-password").value = "";
    document.getElementById("modal-admin-error").textContent = "";
    document.getElementById("modal-admin").style.display = "flex";
    document.getElementById("new-admin-nombre").focus();
}

/** Cierra el modal de creación de admin. */
function cerrarModalAdmin() {
    document.getElementById("modal-admin").style.display = "none";
}

// Cerrar modal al hacer clic fuera de la card
document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("modal-admin")?.addEventListener("click", (e) => {
        if (e.target === e.currentTarget) cerrarModalAdmin();
    });
    // Cerrar con Escape
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") cerrarModalAdmin();
    });
});

/** Crea un nuevo administrador llamando al endpoint POST /admin/admins. */
async function crearAdmin() {
    const nombre   = document.getElementById("new-admin-nombre").value.trim();
    const username = document.getElementById("new-admin-username").value.trim();
    const password = document.getElementById("new-admin-password").value;
    const errEl    = document.getElementById("modal-admin-error");
    const btn      = document.getElementById("btn-crear-admin");
    errEl.textContent = "";

    if (!nombre || !username || !password) {
        errEl.textContent = "Completa todos los campos.";
        return;
    }
    if (password.length < 6) {
        errEl.textContent = "La contraseña debe tener al menos 6 caracteres.";
        return;
    }

    btn.disabled = true;
    btn.textContent = "Creando…";

    try {
        const res = await fetch("/admin/admins", {
            method: "POST",
            headers: { "Content-Type": "application/json", ...(_authHeaders()) },
            body: JSON.stringify({ nombre, username, password }),
        });

        if (res.status === 400) {
            const data = await res.json();
            errEl.textContent = data.detail ?? "El usuario ya existe.";
            return;
        }
        if (!res.ok) {
            errEl.textContent = "Error al crear el admin. Intenta de nuevo.";
            return;
        }

        cerrarModalAdmin();
        // Recarga solo la lista de admins
        const listRes  = await fetch("/admin/admins", { headers: _authHeaders() });
        const admins   = await listRes.json();
        renderAdmins(admins);
    } catch (e) {
        errEl.textContent = "Error de conexión.";
        console.error(e);
    } finally {
        btn.disabled = false;
        btn.textContent = "Crear admin";
    }
}

/** Desactiva un admin por su ID. */
async function desactivarAdmin(adminId) {
    if (!confirm("¿Seguro que quieres desactivar este administrador?")) return;

    try {
        const res = await fetch(`/admin/admins/${adminId}`, {
            method: "DELETE",
            headers: _authHeaders(),
        });

        if (!res.ok) {
            const data = await res.json().catch(() => ({}));
            alert(data.detail ?? "Error al desactivar el admin.");
            return;
        }

        // Recarga la lista
        const listRes = await fetch("/admin/admins", { headers: _authHeaders() });
        const admins  = await listRes.json();
        renderAdmins(admins);
    } catch (e) {
        alert("Error de conexión.");
        console.error(e);
    }
}
