from flask import Flask, render_template, request, jsonify
from database import (
    init_db, get_presupuestos, set_presupuesto, delete_presupuesto,
    get_total_gastado, add_gasto, get_gastos_hoy, delete_gasto,
    get_resumen_completo, get_total_gastado_hoy
)
from sync_sheets import sync_to_sheets

app = Flask(__name__)
init_db()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/resumen", methods=["GET"])
def resumen():
    return jsonify({
        "presupuestos": get_resumen_completo(),
        "gastos_hoy": [
            {"id": g[0], "descripcion": g[1], "monto": g[2],
             "categoria": g[3], "hora": g[4]}
            for g in get_gastos_hoy()
        ],
        "total_gastado_hoy": get_total_gastado_hoy()
    })


@app.route("/api/presupuestos", methods=["GET", "POST"])
def presupuestos():
    if request.method == "POST":
        data = request.json
        set_presupuesto(data["categoria"], data["periodo"], float(data["monto"]))
        return jsonify({"ok": True})
    return jsonify([
        {"categoria": c, "periodo": p, "monto": m}
        for c, p, m in get_presupuestos()
    ])


@app.route("/api/presupuestos/<cat>/<per>", methods=["DELETE"])
def eliminar_presupuesto(cat, per):
    delete_presupuesto(cat, per)
    return jsonify({"ok": True})


@app.route("/api/gastos", methods=["POST"])
def registrar_gasto():
    data = request.json
    descripcion = data["descripcion"]
    monto = float(data["monto"])
    categoria = data["categoria"]

    # Validar contra TODOS los presupuestos de esa categoría
    presupuestos = get_presupuestos()
    bloqueos = []
    detalles = []

    for cat, per, limite in presupuestos:
        if cat.lower() == categoria.lower():
            gastado = get_total_gastado(cat, per)
            disponible = limite - gastado
            nuevo_total = gastado + monto
            detalles.append({
                "categoria": cat,
                "periodo": per,
                "limite": limite,
                "gastado": gastado,
                "disponible": disponible,
                "excedido": nuevo_total > limite
            })
            if nuevo_total > limite:
                bloqueos.append(
                    f"• {per.capitalize()}: ${disponible:.2f} disponible, querés gastar ${monto:.2f}"
                )

    if bloqueos:
        return jsonify({
            "ok": False,
            "bloqueado": True,
            "mensaje": "🚫 NO PODÉS HACER ESTE GASTO\n\n" + "\n".join(bloqueos),
            "detalles": detalles
        }), 403

    add_gasto(descripcion, monto, categoria)
    try: sync_to_sheets()
    except: pass

    return jsonify({
        "ok": True,
        "bloqueado": False,
        "detalles": detalles,
        "mensaje": f"✅ Gasto de ${monto:.2f} registrado"
    })


@app.route("/api/gastos/<int:id>", methods=["DELETE"])
def eliminar_gasto(id):
    delete_gasto(id)
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
