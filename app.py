from datetime import datetime

import streamlit as st
import pandas as pd

from common.var import COINS
from utils.qvapay_api import QvaPay

# Main app
st.title("QvaPay P2P Exchange Insights")

try:
    qva_pay = QvaPay()
except Exception as e:
    st.error(f"Error obteniendo los datos: {e}")


if 'database_updated' not in st.session_state:
    st.session_state.database_updated = False

if not st.session_state.database_updated:
    try:
        qva_pay.update_db()
        st.session_state.database_updated = True
    except Exception as e:
        st.error(f"Error obteniendo los datos: {e}")

# Sidebar configuration
st.sidebar.header("Parámetros")
symbol = st.sidebar.selectbox("Selecciona la moneda", ("GENERAL",) + COINS)
start_date = st.sidebar.date_input("Fecha de inicio", value=datetime.now() - pd.Timedelta(days=365))
end_date = st.sidebar.date_input("Fecha de cierre", value=datetime.now())
update_btn = st.sidebar.button("Actualizar datos")

if update_btn:
    try:
        qva_pay.update_db()
    except Exception as e:
        st.error(f"Error obteniendo los datos: {e}")


if symbol == "GENERAL":
    st.subheader("General")
    top = st.number_input("Top Market Makers", value=10, step=1)
    market_maker = qva_pay.get_users_info_by_id(qva_pay.get_market_makers(10, "all"))
    for index, user in enumerate(reversed(market_maker)):
        st.write(f"{index+1} - Nombre: {user["name"]} {user["lastname"]}")
        st.write(f"Total: ${qva_pay.user_coin_query[user["uuid"]]["all"]}")
else:
    st.subheader(f" Datos de {symbol}")
    st.subheader(f" Datos de {symbol}")
    oferta, demanda = qva_pay.get_supply(symbol, start_date, end_date)
    compra, venta = qva_pay.get_spread(symbol, start_date, end_date) 
    st.text(f"Total de oferta: ${oferta}")
    st.text(f"Total de demanda: ${demanda}")
    st.text(f"Spread: ${abs(compra-venta)}")
    st.text(f"Precio de compra: ${compra}")
    st.text(f"Precio de venta: ${venta}")

# Footer
st.markdown("---")
st.caption("© 2023 Streamlit App. All rights reserved.")
