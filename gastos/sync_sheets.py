import gspread
from google.oauth2.service_account import Credentials
from database import get_all_gastos, get_limite

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
SHEET_ID = "111121145548865586337"  # Cambiar por tu Sheet ID

def sync_to_sheets():
    creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
    client = gspread.authorize(creds)

    try:
        sheet = client.open_by_key(SHEET_ID).sheet1
    except:
        sh = client.create("Control de Gastos")
        sh.share("tu_email@gmail.com", perm_type="user", role="owner")
        sheet = sh.sheet1

    gastos = get_all_gastos()
    limite = get_limite()

    # Limpiar y reescribir
    sheet.clear()
    sheet.update("A1:F1", [["ID", "Descripción", "Monto", "Categoría", "Fecha", "Hora"]])
    if gastos:
        filas = [[g[0], g[1], g[2], g[3], g[4], g[5]] for g in gastos]
        sheet.update(f"A2:F{len(filas)+1}", filas)

    # Fila de resumen al final
    fila_resumen = len(gastos) + 3
    sheet.update(f"A{fila_resumen}:B{fila_resumen}", [["LÍMITE DIARIO", limite]])
    print(f"✅ Sincronizado: {len(gastos)} gastos")
