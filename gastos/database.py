import sqlite3
from datetime import datetime, date, timedelta

DB_NAME = "gastos.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Gastos
    c.execute('''
        CREATE TABLE IF NOT EXISTS gastos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descripcion TEXT NOT NULL,
            monto REAL NOT NULL,
            categoria TEXT NOT NULL,
            periodo TEXT NOT NULL,
            fecha TEXT NOT NULL,
            hora TEXT NOT NULL
        )
    ''')

    # Presupuestos (uno por categoría + período)
    c.execute('''
        CREATE TABLE IF NOT EXISTS presupuestos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            categoria TEXT NOT NULL,
            periodo TEXT NOT NULL,
            monto REAL NOT NULL,
            UNIQUE(categoria, periodo)
        )
    ''')

    # Insertar valores por defecto solo si la tabla está vacía
    c.execute("SELECT COUNT(*) FROM presupuestos")
    if c.fetchone()[0] == 0:
        defaults = [
            ("Comida", "diario", 10.00),
            ("Pasaje", "diario", 3.00),
            ("Supermercado", "semanal", 80.00),
            ("Supermercado", "mensual", 470.00),
        ]
        c.executemany(
            "INSERT INTO presupuestos (categoria, periodo, monto) VALUES (?, ?, ?)",
            defaults
        )

    conn.commit()
    conn.close()


# ============== PRESUPUESTOS ==============

def get_presupuestos():
    """Devuelve dict {(categoria, periodo): monto}"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT categoria, periodo, monto FROM presupuestos")
    rows = c.fetchall()
    conn.close()
    return {(r[0], r[1]): r[2] for r in rows}


def set_presupuesto(categoria, periodo, monto):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        "INSERT OR REPLACE INTO presupuestos (categoria, periodo, monto) VALUES (?, ?, ?)",
        (categoria, periodo, monto)
    )
    conn.commit()
    conn.close()


def get_presupuesto(categoria, periodo):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        "SELECT monto FROM presupuestos WHERE categoria=? AND periodo=?",
        (categoria, periodo)
    )
    row = c.fetchone()
    conn.close()
    return row[0] if row else 0


# ============== GASTOS ==============

def add_gasto(descripcion, monto, categoria):
    """Guarda el gasto en el período correcto según la fecha"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    ahora = datetime.now()
    c.execute(
        "INSERT INTO gastos (descripcion, monto, categoria, periodo, fecha, hora) VALUES (?, ?, ?, ?, ?, ?)",
        (descripcion, monto, categoria, "diario", ahora.strftime("%Y-%m-%d"), ahora.strftime("%H:%M:%S"))
    )
    conn.commit()
    conn.close()


def get_gastos_periodo(categoria, periodo):
    """Devuelve el total gastado en una categoría + período"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    hoy = date.today()
    fecha_inicio, fecha_fin = calcular_rango(periodo, hoy)

    c.execute(
        "SELECT COALESCE(SUM(monto), 0) FROM gastos WHERE categoria=? AND fecha BETWEEN ? AND ?",
        (categoria, fecha_inicio, fecha_fin)
    )
    total = c.fetchone()[0]
    conn.close()
    return total


def get_gastos_hoy_detalle():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        "SELECT id, descripcion, monto, categoria, fecha, hora FROM gastos WHERE fecha=? ORDER BY id DESC",
        (date.today().strftime("%Y-%m-%d"),)
    )
    rows = c.fetchall()
    conn.close()
    return rows


def delete_gasto(id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM gastos WHERE id=?", (id,))
    conn.commit()
    conn.close()


# ============== HELPERS ==============

def calcular_rango(periodo, fecha_ref):
    """Devuelve (fecha_inicio, fecha_fin) según el período"""
    if periodo == "diario":
        inicio = fin = fecha_ref.strftime("%Y-%m-%d")
    elif periodo == "semanal":
        # Semana desde lunes a domingo
        inicio_semana = fecha_ref - timedelta(days=fecha_ref.weekday())
        fin_semana = inicio_semana + timedelta(days=6)
        inicio = inicio_semana.strftime("%Y-%m-%d")
        fin = fin_semana.strftime("%Y-%m-%d")
    elif periodo == "mensual":
        inicio = fecha_ref.replace(day=1).strftime("%Y-%m-%d")
        # último día del mes
        if fecha_ref.month == 12:
            fin = fecha_ref.replace(day=31).strftime("%Y-%m-%d")
        else:
            next_month = fecha_ref.replace(month=fecha_ref.month + 1, day=1)
            fin = (next_month - timedelta(days=1)).strftime("%Y-%m-%d")
    return inicio, fin


def get_resumen_completo():
    """Devuelve el estado actual de TODOS los presupuestos"""
    presupuestos = get_presupuestos()
    resumen = []
    for (cat, per), monto in presupuestos.items():
        gastado = get_gastos_periodo(cat, per)
        resumen.append({
            "categoria": cat,
            "periodo": per,
            "limite": monto,
            "gastado": gastado,
            "disponible": monto - gastado,
            "porcentaje": (gastado / monto * 100) if monto > 0 else 0,
            "excedido": gastado > monto
        })
    return resumen
