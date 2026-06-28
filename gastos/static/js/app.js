const API = "";

const ICONOS = {
    "Comida": "🍔", "Pasaje": "🚌", "Supermercado": "🛒",
    "Ocio": "🎮", "Transporte": "🚗", "Salud": "💊",
    "Hogar": "🏠", "General": "📦"
};

const PERIODOS = ["diario", "semanal", "mensual"];

let presupuestosCache = [];

document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("fecha-actual").textContent =
        new Date().toLocaleDateString("es-PA", {
            weekday: "long", day: "numeric", month: "long"
        });
    cargarDatos();
    document.getElementById("form-gasto").addEventListener("submit", registrarGasto);
});

async function cargarDatos() {
    try {
        const res = await fetch(`${API}/api/resumen`);
        const data = await res.json();
        renderResumen(data);
        renderPresupuestos(data.presupuestos);
        renderSelectCategorias(data.presupuestos);
        renderGastos(data.gastos_hoy);
    } catch (e) {
        console.error("Error cargando:", e);
    }
}

function renderResumen(data) {
    let disponibleHoy = 0;
    let limiteHoy = 0;
    data.presupuestos.forEach(p => {
        if (p.periodo === "diario") {
            limiteHoy += p.limite;
            disponibleHoy += Math.max(0, p.disponible);
        }
    });

    document.getElementById("total-disponible").textContent = `$${disponibleHoy.toFixed(2)}`;
    document.getElementById("total-limite").textContent = `de $${limiteHoy.toFixed(2)} hoy`;
    document.getElementById("total-gastado").textContent = `$${data.total_gastado_hoy.toFixed(2)}`;
    document.getElementById("cantidad-gastos").textContent = `${data.gastos_hoy.length} gastos`;
}

function renderSelectCategorias(presupuestos) {
    const select = document.getElementById("categoria");
    const catsUnicas = [...new Set(presupuestos.map(p => p.categoria))];
    select.innerHTML = '<option value="">Seleccionar categoría</option>';
    catsUnicas.forEach(cat => {
        const icon = ICONOS[cat] || "📦";
        select.innerHTML += `<option value="${cat}">${icon} ${cat}</option>`;
    });
}

function renderPresupuestos(presupuestos) {
    const cont = document.getElementById("presupuestos-container");
    cont.innerHTML = "";

    if (presupuestos.length === 0) {
        cont.innerHTML = '<p class="vacio">No hay presupuestos. Tocá ⚙️ para crear.</p>';
        return;
    }

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
                    <span class="label-mini">Límite: <span class="valor-mini">$${p.limite.toFixed(2)}</span></span>
                    <span class="label-mini">Gastado: <span class="valor-mini">$${p.gastado.toFixed(2)}</span></span>
                </div>
                <div class="pres-disponible">
                    ${p.disponible >= 0 ? '💵 $' + p.disponible.toFixed(2) : '🚫 -$' + Math.abs(p.disponible).toFixed(2)}
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
        lista.innerHTML = '<li class="vacio">No hay gastos hoy 🎉</li>';
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

    if (!categoria) {
        mostrarToast("Seleccioná una categoría", "error");
        return;
    }

    const res = await fetch(`${API}/api/gastos`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ descripcion, monto, categoria })
    });
    const data = await res.json();

    if (data.bloqueado) {
        mostrarAlerta(data.mensaje, data.detalles);
    } else if (data.ok) {
        mostrarExito(data.mensaje);
        document.getElementById("form-gasto").reset();
        cargarDatos();
    }
}

function mostrarAlerta(mensaje, detalles) {
    document.getElementById("modal-mensaje").textContent = mensaje;
    const detDiv = document.getElementById("modal-detalles");
    if (detalles) {
        detDiv.innerHTML = detalles.map(d => `
            <div>
                <span><strong>${d.categoria}</strong> (${d.periodo})</span>
                <span>$${d.disponible.toFixed(2)} / $${d.limite.toFixed(2)}</span>
            </div>
        `).join("");
    }
    document.getElementById("modal-alerta").classList.add("active");
    if (navigator.vibrate) navigator.vibrate([300, 100, 300]);
}

function cerrarModal() {
    document.getElementById("modal-alerta").classList.remove("active");
}

function mostrarExito(mensaje) {
    document.getElementById("exito-mensaje").textContent = mensaje;
    document.getElementById("modal-exito").classList.add("active");
    setTimeout(() => cerrarExito(), 1500);
}

function cerrarExito() {
    document.getElementById("modal-exito").classList.remove("active");
}

async function eliminarGasto(id) {
    if (!confirm("¿Eliminar este gasto?")) return;
    await fetch(`${API}/api/gastos/${id}`, { method: "DELETE" });
    cargarDatos();
    mostrarToast("Gasto eliminado", "success");
}

async function abrirPresupuestos() {
    const res = await fetch(`${API}/api/presupuestos`);
    presupuestosCache = await res.json();
    renderEditor();
    document.getElementById("modal-presupuestos").classList.add("active");
}

function renderEditor() {
    const cont = document.getElementById("presupuestos-edit");
    cont.innerHTML = "";

    if (presupuestosCache.length === 0) {
        cont.innerHTML = '<p class="vacio">Tocá "Agregar presupuesto" para empezar</p>';
        return;
    }

    presupuestosCache.forEach((p, i) => {
        const icon = ICONOS[p.categoria] || "📦";
        cont.innerHTML += `
            <div class="pres-edit">
                <input type="text" value="${icon} ${p.categoria}" readonly style="background:#f5f5f5;">
                <select id="per-${i}">
                    ${PERIODOS.map(per => `<option value="${per}" ${per===p.periodo?'selected':''}>${per}</option>`).join('')}
                </select>
                <input type="number" id="mon-${i}" value="${p.monto}" step="0.01" min="0">
                <button onclick="eliminarPres(${i})" title="Eliminar">×</button>
            </div>
        `;
    });
}

function eliminarPres(i) {
    const p = presupuestosCache[i];
    fetch(`${API}/api/presupuestos/${encodeURIComponent(p.categoria)}/${p.periodo}`, {
        method: "DELETE"
    }).then(() => {
        presupuestosCache.splice(i, 1);
        renderEditor();
    });
}

function nuevoPresupuesto() {
    presupuestosCache.push({ categoria: "Nuevo", periodo: "diario", monto: 0 });
    renderEditor();
}

function cerrarPresupuestos() {
    document.getElementById("modal-presupuestos").classList.remove("active");
}

async function guardarPresupuestos() {
    for (let i = 0; i < presupuestosCache.length; i++) {
        const p = presupuestosCache[i];
        const per = document.getElementById(`per-${i}`).value;
        const mon = parseFloat(document.getElementById(`mon-${i}`).value);

        if (isNaN(mon) || mon < 0) {
            mostrarToast("Monto inválido", "error");
            return;
        }

        await fetch(`${API}/api/presupuestos`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ categoria: p.categoria, periodo: per, monto: mon })
        });
    }
    cerrarPresupuestos();
    mostrarToast("✅ Guardado", "success");
    cargarDatos();
}

async function sincronizar() {
    mostrarToast("Sincronizando...", "success");
    const res = await fetch(`${API}/api/sync`, { method: "POST" });
    const data = await res.json();
    mostrarToast(data.ok ? "☁️ Sincronizado" : "Error", data.ok ? "success" : "error");
}

function mostrarToast(msg, tipo = "") {
    const toast = document.getElementById("toast");
    toast.textContent = msg;
    toast.className = `toast show ${tipo}`;
    setTimeout(() => toast.classList.remove("show"), 3000);
}
