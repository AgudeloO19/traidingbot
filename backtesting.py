import MetaTrader5 as mt5
import pandas as pd

SYMBOL = "EURUSD"
TIMEFRAME = mt5.TIMEFRAME_M5
TP = 0.0010
SL = 0.0010

mt5.initialize(
    path="C:\\Program Files\\MetaTrader 5\\terminal64.exe",
    login=40514846,
    password="Monedero42.",
    server="Deriv-Demo"
)

# Descargar datos históricos
rates = mt5.copy_rates_from_pos(SYMBOL, TIMEFRAME, 0, 2000)
df = pd.DataFrame(rates)
df['cuerpo'] = (df['open'] + df['close']) / 2
df['prev1'] = df['cuerpo'].shift(1)
df['prev2'] = df['cuerpo'].shift(2)
df['hh'] = (df['cuerpo'] > df['prev1']) & (df['prev1'] > df['prev2'])
df['ll'] = (df['cuerpo'] < df['prev1']) & (df['prev1'] < df['prev2'])

tendencia_actual = None
resultados = []

for i in range(20, len(df) - 12):  # espacio para mirar las velas futuras
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

    # SOLO operar si la tendencia es nueva (cambia respecto a la anterior)
    if nueva and nueva != tendencia_actual:
        tendencia_actual = nueva
        resultado = "sin resultado"
        entry_price = precio_actual
        future_df = df.iloc[i+1:i+13]

        if nueva == "alcista":
            for _, row in future_df.iterrows():
                if row['high'] >= entry_price + TP:
                    resultado = "TP"
                    break
                if row['low'] <= entry_price - SL:
                    resultado = "SL"
                    break
        elif nueva == "bajista":
            for _, row in future_df.iterrows():
                if row['low'] <= entry_price - TP:
                    resultado = "TP"
                    break
                if row['high'] >= entry_price + SL:
                    resultado = "SL"
                    break

        resultados.append({
            "fecha": timestamp,
            "tendencia": nueva,
            "precio_entrada": entry_price,
            "resultado": resultado
        })

# Guardar resultados en CSV
df_resultados = pd.DataFrame(resultados)
df_resultados.to_csv("resultados_backtest.csv", index=False)
print("✅ Backtesting completado. Archivo guardado como 'resultados_backtest.csv'")
