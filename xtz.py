# --- IMPORTS (Inicio del archivo) ---
import MetaTrader5 as mt5
import pandas as pd
import time
import os
import logging  # 👈 AÑADE ESTA LÍNEA
import csv
from datetime import datetime

# --- CONFIGURACIÓN DEL LOGGING (después de imports) ---
logging.basicConfig(
    filename='logs_bot.txt',
    filemode='a',
    format='%(asctime)s - %(message)s',
    level=logging.INFO
)

# --- FUNCION AUXILIAR PARA LOGUEAR ---
def log(msg):
    print(msg)
    logging.info(msg)

# --- CONEXIÓN A MT5 ---
mt5.initialize(
    path="C:\\Program Files\\MetaTrader 5\\terminal64.exe",
    login=40514846,
    password="Monedero42.",
    server="Deriv-Demo"
)

SYMBOL = "EURUSD"
TIMEFRAME = mt5.TIMEFRAME_M5
tendencia_actual = None

# --- FUNCIONES DE MERCADO ---
def get_market_structure():
    rates = mt5.copy_rates_from_pos(SYMBOL, TIMEFRAME, 0, 100)
    if rates is None or len(rates) == 0:
        return None, None

    df = pd.DataFrame(rates)
    
    # Cálculo del cuerpo (promedio entre open y close)
    df['cuerpo'] = (df['open'] + df['close']) / 2
    df['prev1'] = df['cuerpo'].shift(1)
    df['prev2'] = df['cuerpo'].shift(2)

    # Picos usando solo cuerpos
    hh = df[(df['cuerpo'] > df['prev1']) & (df['prev1'] > df['prev2'])]
    ll = df[(df['cuerpo'] < df['prev1']) & (df['prev1'] < df['prev2'])]

    return hh, ll


def detectar_tendencia(hh, ll):
    global tendencia_actual
    if len(hh) < 2 or len(ll) < 2:
        return None, 0

    precio_actual = mt5.symbol_info_tick(SYMBOL).ask

    # Usar el cuerpo como referencia
    ultima_hh = hh.iloc[-1]['cuerpo']
    ultima_ll = ll.iloc[-1]['cuerpo']

    nueva = None
    if precio_actual > ultima_hh:
        nueva = "alcista"
    elif precio_actual < ultima_ll:
        nueva = "bajista"

    if nueva and nueva != tendencia_actual:
        tendencia_actual = nueva
        return nueva, precio_actual

    return None, precio_actual


# --- GUARDAR SEÑAL ---
def guardar_senal(tendencia, precio):
    # Ruta al archivo de texto de MetaTrader
    ruta_txt = r"C:\Users\Ricardo\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Files\senal_tendencia.txt"

    # Ruta al CSV donde se guarda el historial de cambios
    ruta_csv = "cambios_tendencia_real.csv"

    try:
        # Guardar la señal en el archivo TXT
        with open(ruta_txt, "w") as f:
            f.write(f"{tendencia},{precio}")
        log(f"📝 Señal guardada: {tendencia} @ {precio}")
    except Exception as e:
        log(f"❌ Error al guardar señal TXT: {e}")

    try:
        # Añadir al CSV
        fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        encabezados = ["fecha", "tendencia", "precio"]

        archivo_nuevo = not os.path.exists(ruta_csv)
        with open(ruta_csv, "a", newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=encabezados)
            if archivo_nuevo:
                writer.writeheader()
            writer.writerow({"fecha": fecha_actual, "tendencia": tendencia, "precio": precio})
        log("📌 Registro de tendencia guardado en CSV")
    except Exception as e:
        log(f"❌ Error al guardar en CSV: {e}")

# --- LOOP PRINCIPAL ---
def run_bot():
    log("🚀 Iniciando bot con logging y guardado de señales...")
    while True:
        hh, ll = get_market_structure()
        if hh is None or ll is None:
            time.sleep(60)
            continue
        tendencia, precio = detectar_tendencia(hh, ll)
        log(f"📈 Precio actual: {precio}")
        if tendencia:
            log(f"🔄 Tendencia detectada: {tendencia}")
            guardar_senal(tendencia, precio)
        time.sleep(60)

run_bot()
