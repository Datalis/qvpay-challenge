from datetime import datetime

import streamlit as st
import pandas as pd

from common.var import COINS
from utils.qvapay_api import QvaPay
from utils.helpers import get_date_chart

# Main app
st.title("QvaPay P2P Exchange Insights")

if 'qva_pay' not in st.session_state:
    st.session_state.qva_pay = QvaPay()

if 'database_updated' not in st.session_state:
    st.session_state.database_updated = False

if not st.session_state.database_updated:
    try:
        st.session_state.qva_pay.update_db()
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
        st.session_state.qva_pay.update_db()
    except Exception as e:
        st.error(f"Error obteniendo los datos: {e}")


if symbol == "GENERAL":
    st.subheader("General")
    top = st.number_input("Top Market Makers", value=10, step=1)
    market_maker = st.session_state.qva_pay.get_users_info_by_id(st.session_state.qva_pay.get_market_makers(100, "all"))
    for index, user in enumerate(reversed(market_maker)):
        st.write(f"{index+1} - Nombre: {user["name"]} {user["lastname"]}")
        st.write(f"Total: ${st.session_state.qva_pay.user_coin_query[user["uuid"]]["all"]}")
else:
    st.subheader(f" Datos de {symbol}")
    oferta, demanda = st.session_state.qva_pay.get_supply(symbol, start_date, end_date)
    compra, venta = st.session_state.qva_pay.get_spread(symbol, start_date, end_date) 
    st.text(f"Total de oferta: ${oferta}")
    st.text(f"Total de demanda: ${demanda}")
    if compra == 0 or venta == 0:
        if compra == 0:
            st.write("Spread no disponible. Solo existen ordenes de venta")
        else:
            st.write("Spread no disponible. Solo existen ordenes de compra")
    else:
        st.text(f"Spread: ${abs(compra-venta)}")
        st.text(f"Precio de compra: ${compra}")
        st.text(f"Precio de venta: ${venta}")
    st.subheader("Spread de los Market Makers")
    top = st.number_input("Top Market Makers", value=10, step=1)
    spreads = st.session_state.qva_pay.get_market_makers_spread(top, symbol,start_date, end_date)
    fig = get_date_chart(spreads)
    st.pyplot(fig)


# Footer
st.markdown("---")
st.caption("© 2023 Streamlit App. All rights reserved.")
