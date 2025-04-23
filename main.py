import pandas as pd
import matplotlib.pyplot as plt

# Configuración del backtest
R_R_ratio = 2  # Relación riesgo-recompensa (modifiable)
initial_balance = 100000  # Capital inicial en USD
risk_per_trade = 0.01  # 1% de riesgo por operación
balance = initial_balance  # Balance de la cuenta

# Cargar el archivo con tabulaciones como separador
file_path = "EURUSD_M30_2025.csv"
df = pd.read_csv(file_path, sep='\t')

# Renombrar columnas eliminando los caracteres '<' y '>'
df.columns = [col.strip('<>') for col in df.columns]

# Combinar DATE y TIME en una sola columna de tipo datetime
df['DATETIME'] = pd.to_datetime(df['DATE'] + ' ' + df['TIME'])

# Eliminar columnas DATE y TIME ya que ahora están combinadas en DATETIME
df = df.drop(columns=['DATE', 'TIME'])

# Filtrar todas las velas de 16:00 (GMT+2)
velas_16 = df[df["DATETIME"].dt.time == pd.to_datetime("16:00").time()]

# Lista para almacenar resultados del backtest
backtest_results = []

# --- BACKTESTING ---
for _, vela_clave in velas_16.iterrows():
    high_16 = vela_clave["HIGH"]
    low_16 = vela_clave["LOW"]
    mid_16 = (high_16 + low_16) / 2  # Nivel del 50% de la vela clave
    open_16 = vela_clave["OPEN"]
    close_16 = vela_clave["CLOSE"]

    # Filtrar velas después de la vela clave
    df_after_16 = df[df["DATETIME"] > vela_clave["DATETIME"]]

    trade_type = None
    entry_price = None
    stop_loss = None
    take_profit = None
    trade_result = "No Trade"
    profit_loss = 0  # PnL de la operación
    pending_order = None  # Variable para almacenar la orden pendiente

    # *** PRIMERO: ESPERAMOS A QUE EL PRECIO ROMPA EL HIGH O LOW ***
    for _, row in df_after_16.iterrows():
        if row["HIGH"] > high_16:  # Rompió el alto de la vela clave → Buscamos compra
            trade_type = "BUY"
            pending_order = mid_16  # La orden se coloca en el 50%
            # pending_order = high_16 # La orden se coloca cuando rompa el high
            stop_loss = low_16
            take_profit = pending_order + R_R_ratio * (pending_order - stop_loss)
            break
        elif row["LOW"] < low_16:  # Rompió el bajo de la vela clave → Buscamos venta
            trade_type = "SELL"
            pending_order = mid_16  # La orden se coloca en el 50%
            # pending_order = low_16 # La orden se coloca cuando rompa el low
            stop_loss = high_16
            take_profit = pending_order - R_R_ratio * (stop_loss - pending_order)
            break

    # *** SEGUNDO: ESPERAMOS A QUE EL PRECIO REGRESE AL 50% Y ACTIVE LA ORDEN ***
    if trade_type:
        for _, row in df_after_16.iterrows():
            if trade_type == "BUY" and row["LOW"] <= pending_order:  # Activar compra
                entry_price = pending_order
                break
            elif trade_type == "SELL" and row["HIGH"] >= pending_order:  # Activar venta
                entry_price = pending_order
                break

    # Si no se activó la orden, se descarta la operación
    if entry_price is None:
        continue

    print(f"Fecha: {vela_clave['DATETIME']}, Tipo: {trade_type}, Entrada: {entry_price}, SL: {stop_loss}, TP: {take_profit}")

    # *** TERCERO: EVALUAMOS SI SE ALCANZA SL O TP PRIMERO ***
    for _, row in df_after_16.iterrows():
        if trade_type == "BUY":
            if row["LOW"] <= stop_loss:
                trade_result = "SL"
                profit_loss = - (balance * risk_per_trade)  # Pérdida del 1% del balance
                break
            if row["HIGH"] >= take_profit:
                trade_result = "TP"
                profit_loss = (balance * risk_per_trade) * R_R_ratio  # Ganancia según R:R
                break
        elif trade_type == "SELL":
            if row["HIGH"] >= stop_loss:
                trade_result = "SL"
                profit_loss = - (balance * risk_per_trade)
                break
            if row["LOW"] <= take_profit:
                trade_result = "TP"
                profit_loss = (balance * risk_per_trade) * R_R_ratio
                break

    # Actualizar balance
    balance += profit_loss

    # Guardar resultado en la lista
    backtest_results.append({
        "Fecha": vela_clave["DATETIME"],
        "Tipo": trade_type,
        "Entrada": entry_price,
        "SL": stop_loss,
        "TP": take_profit,
        "Resultado": trade_result,
        "P&L (USD)": profit_loss,
        "Balance (USD)": balance
    })

# --- ANÁLISIS DE RESULTADOS ---
df_results = pd.DataFrame(backtest_results)

# Contar operaciones
total_trades = len(df_results[df_results["Tipo"].notnull()])
wins = len(df_results[df_results["Resultado"] == "TP"])
losses = len(df_results[df_results["Resultado"] == "SL"])
win_rate = (wins / total_trades) * 100 if total_trades > 0 else 0
roi = (balance - initial_balance) / initial_balance * 100

# Mostrar estadísticas
print("\n📊 **Backtesting Results** 📊")
print(f"📅 Total Trades: {total_trades}")
print(f"✅ Wins (TP): {wins}")
print(f"❌ Losses (SL): {losses}")
print(f"🏆 Win Rate: {win_rate:.2f}%\n")
print(f"🪙 Initial Balance: ${initial_balance} USD")
print(f"💰 Balance Final: ${balance:.2f} USD")
print(f"⚖️ R:R Ratio: {R_R_ratio}")
print(f"📈 ROI: {roi:.2f}%")

# --- VISUALIZACIÓN GRÁFICA ---
plt.figure(figsize=(12, 6))

# Graficar precios
plt.plot(df["DATETIME"], df["CLOSE"], label="Precio de cierre", color='black', linestyle='dotted')

# Dibujar todas las velas clave
for _, row in df_results.iterrows():
    plt.axvline(x=row["Fecha"], color='blue', linestyle='--', alpha=0.5)

# Marcar entradas y resultados
for _, row in df_results.iterrows():
    if row["Tipo"] == "BUY":
        plt.scatter(row["Fecha"], row["Entrada"], color='blue', label="BUY" if "BUY" not in plt.gca().get_legend_handles_labels()[1] else "", zorder=3)
    elif row["Tipo"] == "SELL":
        plt.scatter(row["Fecha"], row["Entrada"], color='red', label="SELL" if "SELL" not in plt.gca().get_legend_handles_labels()[1] else "", zorder=3)

    if row["Resultado"] == "TP":
        plt.scatter(row["Fecha"], row["TP"], color='green', label="TP" if "TP" not in plt.gca().get_legend_handles_labels()[1] else "", marker='^', zorder=3)
    elif row["Resultado"] == "SL":
        plt.scatter(row["Fecha"], row["SL"], color='brown', label="SL" if "SL" not in plt.gca().get_legend_handles_labels()[1] else "", marker='v', zorder=3)

# Configurar la gráfica
plt.legend()
plt.xlabel("Fecha y Hora")
plt.ylabel("Precio XAUUSD")
plt.title("Backtesting Estrategia ICT - Operaciones y Resultados")
plt.xticks(rotation=45)
plt.grid()

# Mostrar la gráfica
plt.show()
