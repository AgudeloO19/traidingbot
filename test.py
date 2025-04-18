import MetaTrader5 as mt5
import pandas as pd

SYMBOL = "EURUSD"
TIMEFRAME = mt5.TIMEFRAME_M5
TP = 0.0010  # 10 pips
SL = 0.0010  # 10 pips
LOTE = 0.1   # 0.1 lotes
VALOR_PIP_USD = 10 * LOTE  # $1 por pip con 0.1 lotes

mt5.initialize(
    path="C:\\Program Files\\MetaTrader 5\\terminal64.exe",
    login=40514846,
    password="Monedero42.",
    server="Deriv-Demo"
)

rates = mt5.copy_rates_from_pos(SYMBOL, TIMEFRAME, 0, 100)
df = pd.DataFrame(rates)
df['cuerpo'] = (df['open'] + df['close']) / 2
df['prev1'] = df['cuerpo'].shift(1)
df['prev2'] = df['cuerpo'].shift(2)
df['hh'] = (df['cuerpo'] > df['prev1']) & (df['prev1'] > df['prev2'])
df['ll'] = (df['cuerpo'] < df['prev1']) & (df['prev1'] < df['prev2'])

tendencia_actual = None
resultados = []

for i in range(20, len(df) - 12):
    sub_df = df.iloc[i - 20:i]
    hh = sub_df[sub_df['hh']]
    ll = sub_df[sub_df['ll']]

    if len(hh) == 0 or len(ll) == 0:
        continue

    ultima_hh = hh.iloc[-1]['cuerpo']
    ultima_ll = ll.iloc[-1]['cuerpo']
    precio_actual = df.iloc[i]['close']
    timestamp = pd.to_datetime(df.iloc[i]['time'], unit='s')

    nueva = None
    if precio_actual > ultima_hh:
        nueva = "alcista"
    elif precio_actual < ultima_ll:
        nueva = "bajista"

    if nueva and nueva != tendencia_actual:
        tendencia_actual = nueva
        resultado = "sin resultado"
        ganancia_usd = 0.0
        entry_price = precio_actual
        future_df = df.iloc[i+1:i+13]

        if nueva == "alcista":
            for _, row in future_df.iterrows():
                if row['high'] >= entry_price + TP:
                    resultado = "TP"
                    ganancia_usd = VALOR_PIP_USD * (TP / 0.0001)
                    break
                if row['low'] <= entry_price - SL:
                    resultado = "SL"
                    ganancia_usd = -VALOR_PIP_USD * (SL / 0.0001)
                    break
        elif nueva == "bajista":
            for _, row in future_df.iterrows():
                if row['low'] <= entry_price - TP:
                    resultado = "TP"
                    ganancia_usd = VALOR_PIP_USD * (TP / 0.0001)
                    break
                if row['high'] >= entry_price + SL:
                    resultado = "SL"
                    ganancia_usd = -VALOR_PIP_USD * (SL / 0.0001)
                    break

        resultados.append({
            "fecha": timestamp,
            "tendencia": nueva,
            "precio_entrada": entry_price,
            "resultado": resultado,
            "ganancia_usd": round(ganancia_usd, 2)
        })

# Guardar en CSV
df_resultados = pd.DataFrame(resultados)
df_resultados.to_csv("resultados_backtest.csv", index=False)
print("✅ Backtesting completado. Archivo guardado como 'resultados_backtest.csv'")

# Mostrar resumen final
ganancia_total = df_resultados['ganancia_usd'].sum()
print(f"💰 Ganancia total del sistema: ${ganancia_total:.2f} USD")
