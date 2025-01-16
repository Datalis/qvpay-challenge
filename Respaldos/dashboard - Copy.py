import pandas as pd
import requests
import json
import logging
from dash import Dash, dcc, html, Input, Output, dash_table
import plotly.express as px
from datetime import datetime

# Configurar el logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configurar el logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# # Descargar y procesar los datos de la API
# logger.info("Starting data fetch from API...")
# base = []
# path = "https://qvapay.com/api/p2p"

# def get_data(path):
#     logger.debug(f"Fetching data from: {path}")
#     response = requests.get(path)
#     logger.debug(f"Response status code: {response.status_code}")
#     return response.json()

# while path:
#     data = get_data(path)
#     base.extend(data['data'])
#     path = data['next_page_url']
#     logger.info(f"Fetched {len(data['data'])} records. Next page: {path}")

# # Guardar los datos en un archivo JSON para referencia
# current_time = datetime.now()
# filename_date = current_time.strftime("%Y-%m-%d_%H-%M-%S")
# with open(f"base{filename_date}.json", "w") as file:
#     json.dump(base, file, indent=4)
# logger.info(f"Data saved to base{filename_date}.json")

# Leer el archivo JSON
json_file_path = './base2025-01-15_04-59-16.json'
with open(json_file_path, 'r') as file:
    base = json.load(file)

# Crear DataFrame
base_df = pd.DataFrame(base)
logger.debug(f"DataFrame created with {len(base_df)} records.")

# Procesar y filtrar los datos
try:
    base_df["date"] = base_df["updated_at"]
    filtered_base = pd.DataFrame({
        'id': base_df['uuid'],
        'date': pd.to_datetime(base_df['date']).dt.date,
        'user': base_df['owner'].apply(lambda x: x.get('username', 'Unknown')),
        'coin': base_df['coin'],
        'type': base_df['type'],
        'amount': pd.to_numeric(base_df["amount"], errors='coerce'),
        'receive': pd.to_numeric(base_df["receive"], errors='coerce'),
    })
    filtered_base['price'] = filtered_base["receive"] / filtered_base["amount"]
    logger.info("Data filtering completed successfully.")
except Exception as e:
    logger.error(f"Error during data processing: {e}")

# Revisar si el DataFrame está vacío
if filtered_base.empty:
    logger.warning("Filtered base is empty! Check your data source.")

# Agrupar los datos para la tabla
try:
    grouped_data = (
    filtered_base
    .groupby(['coin', 'date', 'type'])
    .agg(
        total_amount=('amount', 'sum'),
        #modal_variance=('price', 'mode'),
        median_price=('price', 'median'),
        mean_price=('price', 'mean'),
        price_variance=('price', 'var')
    )
    .reset_index()
)
    grouped_data.columns = [
        'Moneda', 'Fecha', 'Tipo de ofertas',
        'Oferta total en USDT', 'Mediana de los precios', 'Precio medio', 'Varianza del precio'
    ]
    logger.info("Data grouping completed successfully.")
except Exception as e:
    logger.error(f"Error during data grouping: {e}")

# Inicializar la app Dash
app = Dash(__name__)

# Layout de la app
app.layout = html.Div([
    html.H1("Análisis general de transacciones abiertas en QvaPay", style={'text-align': 'center', 'font-family': 'Calibri'}),
    html.Div([
        html.Label("Seleccionar moneda:",style={'font-family': 'Calibri'}),
        dcc.Dropdown(
            id='coin-selector',
            options=[{'label': coin, 'value': coin} for coin in filtered_base['coin'].unique()],
            value=filtered_base['coin'].unique()[0] if not filtered_base.empty else None,
            style={'width': '90%', 'font-family': 'Calibri'}
        ),
        html.Label("Seleccionar fecha:",style={'font-family': 'Calibri'}),
        dcc.Dropdown(
            id='date-selector',
            options=[{'label': str(date), 'value': str(date)} for date in filtered_base['date'].unique()],
            value=str(filtered_base['date'].unique()[0]) if not filtered_base.empty else None,
            style={'width': '90%', 'font-family': 'Calibri'}
        ),
        html.Label("Seleccionar tipo de oferta:",style={'font-family': 'Calibri'}),
        dcc.RadioItems(
            id='type-selector',
            options=[
                {'label': 'Compra', 'value': 'buy'},
                {'label': 'Venta', 'value': 'sell'}
            ],
            value='buy',
           style={'font-family': 'Calibri'}
        ),
    ], style={
        'background-color': '#f9f9f9', 
        'padding': '10px', 
        'box-shadow': '0px 4px 10px rgba(0,0,0,0.1)'
    }),
    # dcc.Graph(id='transaction-graph'),
    dcc.Graph(id='price-amount-graph'),
    dash_table.DataTable(
        id='summary-table',
        columns=[{"name": col, "id": col} for col in grouped_data.columns] if not grouped_data.empty else [],
        style_table={'overflowX': 'auto', 'font-family': 'Calibri'},
        style_cell={'textAlign': 'center', 'font-family': 'Calibri'},
        style_header={'fontWeight': 'bold', 'font-family': 'Calibri'},
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': 'rgb(248, 248, 248)'
            }
        ],
    )
], style={'background-color': '#f4f4f4', 'margin': '0', 'font-family': 'Calibri'})

# Callbacks
@app.callback(
    [#Output('transaction-graph', 'figure'),
     Output('price-amount-graph', 'figure'),
     Output('summary-table', 'data')],
    [Input('coin-selector', 'value'),
     Input('date-selector', 'value'),
     Input('type-selector', 'value')]
)
def update_dashboard(selected_coin, selected_date, selected_type):
    logger.debug(f"Updating dashboard for Coin: {selected_coin}, Date: {selected_date}, Type: {selected_type}")
    if not selected_coin or not selected_date:
        logger.warning("No valid selection for coin or date.")
        return {}, []

    selected_date = pd.to_datetime(selected_date).date()
    filtered_data = filtered_base[
        (filtered_base['coin'] == selected_coin) &
        (filtered_base['date'] == selected_date) &
        (filtered_base['type'] == selected_type)
    ]

    if filtered_data.empty:
        logger.warning("No data found for the selected filters.")
        return { }, []

    # Gráfico de transacciones
    # fig1 = px.bar(
    #     filtered_data,
    #     x=filtered_data.index,
    #     y='amount',
    #     color='type',
    #     title="Transaction Amounts"
    # )

    # Gráfico de precio vs cantidad
    fig2 = px.scatter(
        filtered_data,
        x='amount',
        y='price',
        title="Precios vs. monto de las ofertas respecto a la mediana de los precios disponibles",
        color='type',
        labels={'amount':'Monto de la oferta', 'price':'Precio del USDT'}
    )
    f = grouped_data[(grouped_data['Fecha'] == selected_date) & (grouped_data['Moneda'] == selected_coin) & (grouped_data['Tipo de ofertas'] == selected_type)]
    logger.info(f)
    value = f['Mediana de los precios']
    logger.info(value)
    fig2.add_hline(value.sum())

    # Datos de la tabla
    filtered_table_data = grouped_data[(grouped_data['Fecha'] == selected_date) & (grouped_data['Tipo de ofertas'] == selected_type)].to_dict('records')
    logger.info(f"Filtered data size: {len(filtered_data)}, Table data size: {len(filtered_table_data)}")
    return fig2, filtered_table_data

# Ejecutar la app
if __name__ == '__main__':
    logger.info("Starting the Dash server...")
    app.run_server(debug=True)
