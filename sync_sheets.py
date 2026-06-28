"""
Sincronización con Google Sheets
Opcional - funciona solo si credentials.json existe
"""
import os

DB_NAME = "gastos.db"

def sync_to_sheets():
    """Sincroniza los gastos a Google Sheets"""
    # Si no hay credenciales, salir silenciosamente
    if not os.path.exists("credentials.json"):
        print("⚠️ credentials.json no existe - sync omitido")
        return False

    try:
        import gspread
        from google.oauth2.service_account import Credentials
        import sqlite3
    except ImportError:
        print("⚠️ Faltan librerías: pip install gspread google-auth")
        return False

    # ID de tu Google Sheet (cambialo por el tuyo)
    SHEET_ID = "PEGAR_AQUI_TU_ID_DE_GOOGLE_SHEET"

    try:
        creds = Credentials.from_service_account_file(
            "credentials.json",
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
        )
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SHEET_ID).sheet1

        # Leer gastos de SQLite
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT id, descripcion, monto, categoria, fecha, hora FROM gastos ORDER BY fecha DESC, id DESC")
        gastos = c.fetchall()

        c.execute("SELECT categoria, periodo, monto FROM presupuestos")
        presupuestos = c.fetchall()
        conn.close()

        # Escribir en Sheets
        sheet.clear()
        sheet.update("A1:F1", [["ID", "Descripción", "Monto", "Categoría", "Fecha", "Hora"]])
        if gastos:
            filas = [list(g) for g in gastos]
            sheet.update(f"A2:F{len(filas)+1}", filas)

        # Sección de presupuestos
        fila_p = len(gastos) + 4
        sheet.update(f"A{fila_p}:C{fila_p}", [["PRESUPUESTOS", "", ""]])
        sheet.update(f"A{fila_p+1}:C{fila_p+1}", [["Categoría", "Período", "Monto"]])
        for i, (cat, per, monto) in enumerate(presupuestos):
            sheet.update(f"A{fila_p+2+i}:C{fila_p+2+i}", [[cat, per, monto]])

        print(f"✅ Sincronizado: {len(gastos)} gastos y {len(presupuestos)} presupuestos")
        return True

    except Exception as e:
        print(f"❌ Error en sync: {e}")
        return False
