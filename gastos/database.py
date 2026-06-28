import sqlite3
from datetime import datetime, date, timedelta

DB_NAME = "gastos.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS gastos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descripcion TEXT NOT NULL,
            monto REAL NOT NULL,
            categoria TEXT NOT NULL,
            fecha TEXT NOT NULL,
            hora TEXT NOT NULL
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS presupuestos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            categoria TEXT NOT NULL,
            periodo TEXT NOT NULL,
            monto REAL NOT NULL,
            UNIQUE(categoria, periodo)
        )
    ''')

    # Valores por defecto
    c.execute("SELECT COUNT(*) FROM presupuestos")
    if c.fetchone()[0] == 0:
        defaults = [
            ("Comida", "diario", 10.00),
            ("Pasaje", "diario", 3.00),
            ("Supermercado", "semanal", 80.00),
            ("Supermercado", "mensual", 470.00),
            ("Ocio", "semanal", 50.00),
            ("Transporte", "semanal", 30.00),
        ]
        c.executemany(
            "INSERT INTO presupuestos (categoria, periodo, monto) VALUES (?, ?, ?)",
            defaults
        )

    conn.commit()
    conn.close()


# ============== PRESUPUESTOS ==============

def get_presupuestos():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT categoria, periodo, monto FROM presupuestos")
    rows = c.fetchall()
    conn.close()
    return [(r[0], r[1], r[2]) for r in rows]


def set_presupuesto(categoria, periodo, monto):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        "INSERT OR REPLACE INTO presupuestos (categoria, periodo, monto) VALUES (?, ?, ?)",
        (categoria, periodo, monto)
    )
    conn.commit()
    conn.close()


def delete_presupuesto(categoria, periodo):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM presupuestos WHERE categoria=? AND periodo=?", (categoria, periodo))
    conn.commit()
    conn.close()


# ============== GASTOS ==============

def add_gasto(descripcion, monto, categoria):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    ahora = datetime.now()
    c.execute(
        "INSERT INTO gastos (descripcion, monto, categoria, fecha, hora) VALUES (?, ?, ?, ?, ?)",
        (descripcion, monto, categoria,
         ahora.strftime("%Y-%m-%d"), ahora.strftime("%H:%M:%S"))
    )
    conn.commit()
    conn.close()


def get_gastos_hoy():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        "SELECT id, descripcion, monto, categoria, hora FROM gastos WHERE fecha=? ORDER BY id DESC",
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


# ============== CÁLCULOS ==============

def calcular_rango(periodo, fecha_ref=None):
    if fecha_ref is None:
        fecha_ref = date.today()

    if periodo == "diario":
        inicio = fin = fecha_ref.strftime("%Y-%m-%d")
    elif periodo == "semanal":
        # Semana de lunes a domingo
        inicio_sem = fecha_ref - timedelta(days=fecha_ref.weekday())
        fin_sem = inicio_sem + timedelta(days=6)
        inicio = inicio_sem.strftime("%Y-%m-%d")
        fin = fin_sem.strftime("%Y-%m-%d")
    elif periodo == "mensual":
        inicio = fecha_ref.replace(day=1).strftime("%Y-%m-%d")
        if fecha_ref.month == 12:
            fin = fecha_ref.replace(day=31).strftime("%Y-%m-%d")
        else:
            prox = fecha_ref.replace(month=fecha_ref.month + 1, day=1)
            fin = (prox - timedelta(days=1)).strftime("%Y-%m-%d")
    return inicio, fin


def get_total_gastado(categoria, periodo):
    """Total gastado en una categoría dentro del período"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    inicio, fin = calcular_rango(periodo)
    c.execute(
        "SELECT COALESCE(SUM(monto), 0) FROM gastos WHERE categoria=? AND fecha BETWEEN ? AND ?",
        (categoria, inicio, fin)
    )
    total = c.fetchone()[0]
    conn.close()
    return total


def get_resumen_completo():
    """Estado de todos los presupuestos con sus cálculos"""
    presupuestos = get_presupuestos()
    resumen = []
    for cat, per, monto in presupuestos:
        gastado = get_total_gastado(cat, per)
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


def get_total_gastado_hoy():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        "SELECT COALESCE(SUM(monto), 0) FROM gastos WHERE fecha=?",
        (date.today().strftime("%Y-%m-%d"),)
    )
    total = c.fetchone()[0]
    conn.close()
    return total
