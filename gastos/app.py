from flask import Flask, render_template, request, jsonify
from database import (
    init_db, get_presupuestos, set_presupuesto, get_presupuesto,
    get_gastos_periodo, add_gasto, get_gastos_hoy_detalle,
    delete_gasto, get_resumen_completo
)
from sync_sheets import sync_to_sheets

app = Flask(__name__)
init_db()

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/resumen", methods=["GET"])
def resumen():
    """Estado de todos los presupuestos"""
    data = get_resumen_completo()
    gastos_hoy = get_gastos_hoy_detalle()
    return jsonify({
        "presupuestos": data,
        "gastos_hoy": [
            {"id": g[0], "descripcion": g[1], "monto": g[2],
             "categoria": g[3], "fecha": g[4], "hora": g[5]}
            for g in gastos_hoy
        ]
    })


@app.route("/api/presupuestos", methods=["GET", "POST"])
def presupuestos():
    if request.method == "POST":
        data = request.json
        set_presupuesto(data["categoria"], data["periodo"], float(data["monto"]))
        # Re-sincronizar
        try: sync_to_sheets()
        except: pass
        return jsonify({"ok": True})
    return jsonify(get_presupuestos_list())


def get_presupuestos_list():
    return [
        {"categoria": k[0], "periodo": k[1], "monto": v}
        for k, v in get_presupuestos().items()
    ]


@app.route("/api/gastos", methods=["POST"])
def registrar_gasto():
    data = request.json
    descripcion = data["descripcion"]
    monto = float(data["monto"])
    categoria = data["categoria"]

    # === VALIDACIÓN PRINCIPAL ===
    presupuestos_cat = get_presupuestos()
    categoria_lower = categoria.lower()

    bloqueos = []
    presupuestos_aplicables = []

    # Buscar presupuestos para esta categoría
    for (cat, per), limite in presupuestos_cat.items():
        if cat.lower() == categoria_lower:
            gastado = get_gastos_periodo(cat, per)
            nuevo_total = gastado + monto
            disponible = limite - gastado
            presupuestos_aplicables.append({
                "categoria": cat,
                "periodo": per,
                "limite": limite,
                "gastado_actual": gastado,
                "disponible": disponible,
                "nuevo_total": nuevo_total,
                "excedido": nuevo_total > limite
            })
            if nuevo_total > limite:
                bloqueos.append(f"{per.capitalize()}: te pasarías (disponible ${disponible:.2f})")

    # Si hay bloqueos en ALGÚN período → no permitir
    if bloqueos:
        return jsonify({
            "ok": False,
            "bloqueado": True,
            "motivo": " | ".join(bloqueos),
            "mensaje": f"🚫 NO PODÉS COMPRAR ESTO.\n\n" + "\n".join(bloqueos),
            "detalles": presupuestos_aplicables
        }), 403

    # Si pasa todas las validaciones → guardar
    add_gasto(descripcion, monto, categoria)

    try: sync_to_sheets()
    except Exception as e: print(f"Sync: {e}")

    return jsonify({
        "ok": True,
        "bloqueado": False,
        "detalles": presupuestos_aplicables,
        "mensaje": f"✅ Gasto registrado. " +
                   " | ".join([f"{p['periodo']}: ${p['disponible'] - monto:.2f} disp."
                               for p in presupuestos_aplicables])
    })


@app.route("/api/gastos/<int:id>", methods=["DELETE"])
def eliminar(id):
    delete_gasto(id)
    try: sync_to_sheets()
    except: pass
    return jsonify({"ok": True})


@app.route("/api/sync", methods=["POST"])
def sync():
    try:
        sync_to_sheets()
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
