import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, time as dt_time, timedelta

# === CONFIGURACIÓN BACKTEST ===
SYMBOL = "XAUUSD"
TIMEFRAME = mt5.TIMEFRAME_M30
R_R_RATIO = 2
RISK_PER_TRADE = 0.01
INITIAL_BALANCE = 10000
TARGET_HOUR = dt_time(16, 0)
VELAS_ANALIZAR = 13200
balance = INITIAL_BALANCE

# === CONEXIÓN MT5 ===
if not mt5.initialize(
    path="C:\\Program Files\\MetaTrader 5\\terminal64.exe",
    login=40514846,
    password="Monedero42.",
    server="Deriv-Demo"
):
    print("❌ Error al conectar MT5")
    quit()

# === DATOS HISTÓRICOS ===
rates = mt5.copy_rates_from_pos(SYMBOL, TIMEFRAME, 0, VELAS_ANALIZAR)
df = pd.DataFrame(rates)
df['time'] = pd.to_datetime(df['time'], unit='s')
df.set_index('time', inplace=True)

resultados = []

# === BACKTEST LOOP ===
for i in range(1, len(df) - 20):
    vela = df.iloc[i]

    if vela.name.time() != TARGET_HOUR:
        continue

    high = vela['high']
    low = vela['low']
    mid = (high + low) / 2
    tipo = None
    sl = None
    tp = None

    # Buscar ruptura en las próximas 4 velas (2h)
    futuro = df.iloc[i+1:i+5]
    for j, row in futuro.iterrows():
        price = row['close']

        if not tipo:
            if price > high:
                tipo = "BUY"
                sl = low
                tp = mid + R_R_RATIO * (mid - low)
            elif price < low:
                tipo = "SELL"
                sl = high
                tp = mid - R_R_RATIO * (high - mid)

        elif tipo and not 'entrada_confirmada' in locals():
            if tipo == "BUY" and row['low'] <= mid:
                entrada = mid
                entrada_confirmada = True
            elif tipo == "SELL" and row['high'] >= mid:
                entrada = mid
                entrada_confirmada = True

        elif 'entrada_confirmada' in locals():
            # Evaluar TP o SL en las próximas 10 velas
            final = df.loc[j:].iloc[:10]
            resultado = None
            for _, eval_row in final.iterrows():
                if tipo == "BUY":
                    if eval_row['low'] <= sl:
                        resultado = "SL"
                        break
                    if eval_row['high'] >= tp:
                        resultado = "TP"
                        break
                else:
                    if eval_row['high'] >= sl:
                        resultado = "SL"
                        break
                    if eval_row['low'] <= tp:
                        resultado = "TP"
                        break
            if resultado:
                ganancia = (R_R_RATIO * balance * RISK_PER_TRADE) if resultado == "TP" else -balance * RISK_PER_TRADE
                balance += ganancia
                resultados.append({
                    "fecha": vela.name,
                    "tipo": tipo,
                    "entrada": entrada,
                    "tp": tp,
                    "sl": sl,
                    "resultado": resultado,
                    "ganancia_usd": round(ganancia, 2),
                    "balance_final": round(balance, 2)
                })
                del entrada_confirmada
                break

# === RESULTADOS ===
df_resultados = pd.DataFrame(resultados)
df_resultados.to_csv("backtest_ICT_XAUUSD.csv", index=False)
print("✅ Backtest completado. Resultados guardados en backtest_ICT_XAUUSD.csv")
print(f"💰 Balance final: {balance:.2f} USD")
