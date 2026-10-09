// ── Estado global ──────────────────────────────────────
let debounceTimer = null;

// ── Registrar listener de búsqueda INMEDIATAMENTE ─────
// (no espera al fetch de evento para no perder el handler)
document.getElementById("buscador").addEventListener("input", function () {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(_ejecutarBusqueda, 280);
});

// ── Inicialización asíncrona ───────────────────────────
(async function init() {
    await obtenerEvento();
})();

// ── Evento activo ──────────────────────────────────────
async function obtenerEvento() {
    try {
        const res = await fetch("/evento/activo");

        if (!res.ok) {
            throw new Error("HTTP " + res.status);
        }

        const data = await res.json();

        console.log("Evento actual/próximo:", data);

    } catch (e) {
        console.error("Error al obtener evento:", e);
    }
}
// ── Búsqueda ───────────────────────────────────────────
async function _ejecutarBusqueda() {
    const texto = document.getElementById("buscador").value.trim();
    const contenedor = document.getElementById("resultados");
    const mensaje = document.getElementById("mensaje");

    if (texto.length < 2) {
        contenedor.innerHTML = "";
        return;
    }

    try {
        const res = await fetch(
            "/buscar?nombre=" + encodeURIComponent(texto)
        );

        if (!res.ok) {
            throw new Error("HTTP " + res.status);
        }

        const data = await res.json();

        // Adaptarse al formato nuevo del backend.
        const resultados = Array.isArray(data)
            ? data
            : data.resultados;

        if (!resultados || resultados.length === 0) {
            contenedor.innerHTML = "";

            if (data.ya_registrado) {
                mostrarToast(
                    "✅ Ya registraste tu asistencia en este evento.",
                    true
                );
            } else {
                contenedor.innerHTML =
                    "<p class=\"no-results\">Sin resultados para \"" +
                    texto.replace(/&/g, "&amp;").replace(/</g, "&lt;") +
                    "\"</p>";
            }

            return;
        }

        if (mensaje) {
            mensaje.textContent = "";
        }

        let html = "";

        for (const j of resultados) {
            const nombreEsc = j.nombre
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/"/g, "&quot;");

            html +=
                '<button type="button" data-id="' + j.id +
                '" data-nombre="' + nombreEsc + '">' +
                nombreEsc +
                "</button>";
        }

        contenedor.innerHTML = html;

        const botones = contenedor.querySelectorAll("button");

        botones.forEach(boton => {
            boton.addEventListener("click", function () {
                const id = Number(this.dataset.id);
                const nombre = this.dataset.nombre;

                document.getElementById("buscador").value = "";
                contenedor.innerHTML = "";

                registrar(id, nombre);
            });
        });

    } catch (e) {
        console.error("Error al buscar:", e);
        mostrarToast("❌ Error al buscar nombres.", false);
    }
}

// ── Registro de asistencia ─────────────────────────────
async function registrar(id, nombre) {
    try {
        console.log("Intentando registrar:", {
            joven_id: id,
            nombre: nombre
        });

        const res = await fetch(
            "/asistencia?joven_id=" + id,
            {
                method: "POST"
            }
        );

    const texto = await res.text();

    console.log("Estado de la respuesta:", res.status);
    console.log("Respuesta del servidor:", texto);

    if (!res.ok) {
        mostrarToast(
            "❌ Error " + res.status + ": " + texto,
            false
        );
        return;
    }

    const data = JSON.parse(texto);

    console.log("Asistencia registrada:", data);

    mostrarToast("✅ Asistencia registrada para " + nombre, true);


} catch (e) {
    console.error("Error completo al registrar:", e);
    mostrarToast("❌ Error de conexión: " + e.message, false);
}
}

function _construirMensaje(nombre, data) {
    if (data.ya_registrado)       return "✅ " + nombre + " — ya estás registrado hoy";
    if (data.es_nueva_racha_max)  return "🏆 " + nombre + " — ¡Nueva racha máxima! " + data.racha_actual + " semanas seguidas";
    if (data.racha_actual > 1)    return "🔥 " + nombre + " — " + data.racha_actual + " semanas en racha";
    return "✔ " + nombre + " — ¡Bienvenido!";
}


// ── Toast de confirmación ──────────────────────────────
var toastTimer = null;

function mostrarToast(texto, esExito) {
    if (esExito === undefined) esExito = true;

    // Actualizar #mensaje legacy
    var msgEl = document.getElementById("mensaje");
    if (msgEl) {
        msgEl.textContent   = texto;
        msgEl.style.color   = esExito ? "var(--color-accent)" : "#ff6b6b";
        msgEl.style.opacity = "1";
    }

    // Toast flotante fijo
    var toast = document.getElementById("toast-asistencia");
    if (!toast) {
        toast    = document.createElement("div");
        toast.id = "toast-asistencia";
        document.body.appendChild(toast);
    }
    toast.textContent = texto;
    toast.className   = esExito ? "toast-visible toast-ok" : "toast-visible toast-err";

    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () {
        toast.className = "toast-hidden";
        if (msgEl) msgEl.style.opacity = "0";
    }, 4000);
}
