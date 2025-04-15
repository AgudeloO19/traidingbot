import MetaTrader5 as mt5
import pandas as pd

SYMBOL = "EURUSD"
TIMEFRAME = mt5.TIMEFRAME_M5

# Inicializar conexión
mt5.initialize(
    path="C:\\Program Files\\MetaTrader 5\\terminal64.exe",
    login=40514846,
    password="Monedero42.",
    server="Deriv-Demo"
)

# Cargar datos históricos
rates = mt5.copy_rates_from_pos(SYMBOL, TIMEFRAME, 0, 2000)
df = pd.DataFrame(rates)

# Cálculo de los cuerpos y estructura del mercado
df['cuerpo'] = (df['open'] + df['close']) / 2
df['prev1'] = df['cuerpo'].shift(1)
df['prev2'] = df['cuerpo'].shift(2)
df['hh'] = (df['cuerpo'] > df['prev1']) & (df['prev1'] > df['prev2'])
df['ll'] = (df['cuerpo'] < df['prev1']) & (df['prev1'] < df['prev2'])

tendencia_actual = None
cambios = []

# Detectar cambios de tendencia
for i in range(20, len(df)):
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
        cambios.append({
            "fecha": timestamp,
            "tendencia": nueva,
            "precio": precio_actual
        })

# Guardar en CSV
df_cambios = pd.DataFrame(cambios)
df_cambios.to_csv("cambios_tendencia.csv", index=False)
print("✅ Registro de cambios de tendencia guardado como 'cambios_tendencia.csv'")
