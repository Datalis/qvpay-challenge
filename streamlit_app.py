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


if symbol == "GENERAL":
    st.subheader("General")
else:
    st.subheader(f" Datos de {symbol}")

# Footer
st.markdown("---")
st.caption("© 2023 Streamlit App. All rights reserved.")
