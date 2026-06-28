const API = "";
const ICONOS = {
    "Comida": "🍔", "Pasaje": "🚌", "Supermercado": "🛒",
    "Ocio": "🎮", "Salud": "💊", "Hogar": "🏠", "General": "📦"
};

document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("fecha-actual").textContent =
        new Date().toLocaleDateString("es-PA", {
            weekday: "long", year: "numeric", month: "long", day: "numeric"
        });
    cargarDatos();
    document.getElementById("form-gasto").addEventListener("submit", registrarGasto);
});


async function cargarDatos() {
    const res = await fetch(`${API}/api/resumen`);
    const data = await res.json();

    renderPresupuestos(data.presupuestos);
    renderGastos(data.gastos_hoy);
}


function renderPresupuestos(presupuestos) {
    const cont = document.getElementById("presupuestos-container");
    cont.innerHTML = `
        <button class="btn-config" onclick="abrirPresupuestos()">⚙️ Editar presupuestos</button>
    `;

    presupuestos.forEach(p => {
        const clase = p.excedido ? "danger" : (p.porcentaje >= 80 ? "warning" : "");
        const icon = ICONOS[p.categoria] || "📦";

        cont.innerHTML += `
            <div class="pres-card ${clase}">
                <div class="pres-header">
                    <span class="pres-titulo">${icon} ${p.categoria}</span>
                    <span class="pres-periodo">${p.periodo}</span>
                </div>
                <div class="pres-montos">
                    <span>Gastado: <span class="gastado">$${p.gastado.toFixed(2)}</span></span>
                    <span>De $${p.limite.toFixed(2)}</span>
                </div>
                <div class="pres-montos">
                    <span></span>
                    <span>Disponible: <span class="disp">$${p.disponible.toFixed(2)}</span></span>
                </div>
                <div class="pres-barra">
                    <div class="pres-barra-fill" style="width: ${Math.min(p.porcentaje, 100)}%"></div>
                </div>
            </div>
        `;
    });
}


function renderGastos(gastos) {
    const lista = document.getElementById("lista-gastos");
    lista.innerHTML = "";
    if (gastos.length === 0) {
        lista.innerHTML = '<li style="justify-content:center;color:#999;padding:20px;">No hay gastos hoy 🎉</li>';
        return;
    }
    gastos.forEach(g => {
        const icon = ICONOS[g.categoria] || "📦";
        lista.innerHTML += `
            <li>
                <div class="gasto-info">
                    <span class="gasto-desc">${icon} ${g.descripcion}</span>
                    <span class="gasto-meta">${g.categoria} · ${g.hora}</span>
                </div>
                <span class="gasto-monto">-$${g.monto.toFixed(2)}</span>
                <button class="btn-eliminar" onclick="eliminarGasto(${g.id})">🗑️</button>
            </li>
        `;
    });
}


async function registrarGasto(e) {
    e.preventDefault();
    const descripcion = document.getElementById("descripcion").value;
    const monto = parseFloat(document.getElementById("monto").value);
    const categoria = document.getElementById("categoria").value;

    const res = await fetch(`${API}/api/gastos`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ descripcion, monto, categoria })
    });
    const data = await res.json();

    if (data.bloqueado) {
        mostrarAlerta(data.mensaje, data.detalles);
    } else if (data.ok) {
        mostrarExito(data.mensaje, data.detalles);
        document.getElementById("form-gasto").reset();
        cargarDatos();
    }
}


function mostrarAlerta(mensaje, detalles) {
    document.getElementById("modal-mensaje").textContent = mensaje;
    const detDiv = document.getElementById("modal-detalles");
    detDiv.innerHTML = detalles.map(d => `
        <div>
            <span><strong>${d.categoria}</strong> (${d.periodo})</span>
            <span>$${d.limite.toFixed(2)} - $${d.gastado_actual.toFixed(2)} = $${d.disponible.toFixed(2)}</span>
        </div>
    `).join("");
    document.getElementById("modal-alerta").classList.add("active");
    if (navigator.vibrate) navigator.vibrate([300, 100, 300, 100, 300]);
}

function cerrarModal() {
    document.getElementById("modal-alerta").classList.remove("active");
}


function mostrarExito(mensaje, detalles) {
    document.getElementById("exito-mensaje").textContent = mensaje;
    const detDiv = document.getElementById("exito-detalles");
    detDiv.innerHTML = detalles.map(d => `
        <div>
            <span><strong>${d.categoria}</strong> (${d.periodo})</span>
            <span>Ahora: $${(d.disponible - parseFloat(document.getElementById("monto").value || 0)).toFixed(2)}</span>
        </div>
    `).join("");
    document.getElementById("modal-exito").classList.add("active");
    setTimeout(() => cerrarExito(), 2000);
}

function cerrarExito() {
    document.getElementById("modal-exito").classList.remove("active");
}


async function eliminarGasto(id) {
    if (!confirm("¿Eliminar?")) return;
    await fetch(`${API}/api/gastos/${id}`, { method: "DELETE" });
    cargarDatos();
    mostrarToast("Eliminado", "success");
}


async function sincronizar() {
    mostrarToast("Sincronizando...", "success");
    const res = await fetch(`${API}/api/sync`, { method: "POST" });
    const data = await res.json();
    mostrarToast(data.ok ? "☁️ Listo" : "Error", data.ok ? "success" : "error");
}


let presupuestosActuales = [];

async function abrirPresupuestos() {
    const res = await fetch(`${API}/api/presupuestos`);
    presupuestosActuales = await res.json();
    const cont = document.getElementById("presupuestos-edit");
    cont.innerHTML = "";

    presupuestosActuales.forEach((p, i) => {
        const icon = ICONOS[p.categoria] || "📦";
        cont.innerHTML += `
            <div class="pres-edit">
                <span style="font-size:18px;">${icon}</span>
                <input type="text" value="${p.categoria}" readonly style="background:#f5f5f5;flex:0.7;">
                <input type="text" value="${p.periodo}" readonly style="background:#f5f5f5;flex:0.5;">
                <input type="number" id="pres-${i}" value="${p.monto}" step="0.01" min="0">
            </div>
        `;
    });

    document.getElementById("modal-presupuestos").classList.add("active");
}

function cerrarPresupuestos() {
    document.getElementById("modal-presupuestos").classList.remove("active");
}

async function guardarPresupuestos() {
    for (let i = 0; i < presupuestosActuales.length; i++) {
        const nuevo = parseFloat(document.getElementById(`pres-${i}`).value);
        if (isNaN(nuevo) || nuevo < 0) {
            mostrarToast("Monto inválido", "error");
            return;
        }
        await fetch(`${API}/api/presupuestos`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                categoria: presupuestosActuales[i].categoria,
                periodo: presupuestosActuales[i].periodo,
                monto: nuevo
            })
        });
    }
    cerrarPresupuestos();
    mostrarToast("✅ Presupuestos actualizados", "success");
    cargarDatos();
}


function mostrarToast(msg, tipo = "") {
    const toast = document.getElementById("toast");
    toast.textContent = msg;
    toast.className = `toast show ${tipo}`;
    setTimeout(() => toast.classList.remove("show"), 3000);
}
