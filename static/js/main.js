// ── Estado global ──────────────────────────────────────
let EVENTO_ID     = null;
let debounceTimer = null;

// ── Registrar listener de búsqueda INMEDIATAMENTE ─────
// (no espera al fetch de evento para no perder el handler)
document.getElementById("buscador").addEventListener("input", function () {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(_ejecutarBusqueda, 280);
});

// ── Inicialización asíncrona (evento + contador) ───────
(async function init() {
    await obtenerEvento();
})();

// ── Evento activo ──────────────────────────────────────
async function obtenerEvento() {
    try {
        const res = await fetch("/evento/activo");
        if (!res.ok) throw new Error("HTTP " + res.status);
        const data = await res.json();
        EVENTO_ID = data.evento_id;
        actualizarContador();
        setInterval(actualizarContador, 10_000);
    } catch (e) {
        console.error("Error al obtener evento:", e);
    }
}

// ── Búsqueda ───────────────────────────────────────────
async function _ejecutarBusqueda() {
    var texto      = document.getElementById("buscador").value.trim();
    var contenedor = document.getElementById("resultados");

    if (texto.length < 2) {
        contenedor.innerHTML = "";
        return;
    }

    try {
        var res  = await fetch("/buscar?nombre=" + encodeURIComponent(texto));
        var data = await res.json();

        if (data.length === 0) {
            contenedor.innerHTML = "<p class=\"no-results\">Sin resultados para \"" + texto + "\"</p>";
            return;
        }

        // Construir botones con data-attributes (sin onclick inline)
        var html = "";
        for (var i = 0; i < data.length; i++) {
            var j = data[i];
            var nombreEsc = j.nombre.replace(/&/g, "&amp;").replace(/"/g, "&quot;");
            html += "<button type=\"button\" data-id=\"" + j.id + "\" data-nombre=\"" + nombreEsc + "\">" + j.nombre + "</button>";
        }
        contenedor.innerHTML = html;

        // Un solo listener de click por botón — funciona en mouse y táctil
        var botones = contenedor.querySelectorAll("button");
        for (var k = 0; k < botones.length; k++) {
            botones[k].addEventListener("click", function () {
                var id     = Number(this.dataset.id);
                var nombre = this.dataset.nombre;
                document.getElementById("buscador").value   = "";
                document.getElementById("resultados").innerHTML = "";
                registrar(id, nombre);
            });
        }

    } catch (e) {
        console.error("Error al buscar:", e);
    }
}

// ── Registro de asistencia ─────────────────────────────
async function registrar(id, nombre) {
    if (!EVENTO_ID) {
        mostrarToast("⏳ Espera un momento e intenta de nuevo...", false);
        return;
    }

   try {
    console.log("Intentando registrar:", {
        joven_id: id,
        nombre: nombre,
        evento_id: EVENTO_ID
    });

    const res = await fetch(
        "/asistencia?joven_id=" + id + "&evento_id=" + EVENTO_ID,
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
    actualizarContador();

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

// ── Contador de asistentes ─────────────────────────────
async function actualizarContador() {
    if (!EVENTO_ID) return;
    try {
        var res  = await fetch("/evento/" + EVENTO_ID + "/conteo");
        var data = await res.json();
        var el   = document.getElementById("contador");
        if (el) el.textContent = "👥 Asistentes hoy: " + data.asistentes;
    } catch (e) {
        console.error("Error al actualizar contador:", e);
    }
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
