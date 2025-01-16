import pandas as pd
import requests
import json
from dash import Dash, dcc, html, Input, Output, dash_table
import plotly.express as px
from datetime import datetime

base=[]
path="https://qvapay.com/api/p2p"

def get_data(path):
    response = requests.get(path)
    return response.json()

while path != None:
    data = get_data(path)
    base.extend(data['data'])
    path=data['next_page_url']

current_time = datetime.now()
filename_date = current_time.strftime("%Y-%m-%d_%H-%M-%S")

with open(f"base{filename_date}.json", "w") as file:
    json.dump(base, file, indent=4)

base_df = pd.DataFrame(base)

base_df["date"] = base_df["updated_at"]

filtered_base = pd.DataFrame({
    'id': base_df['uuid'],
    'date': pd.to_datetime(base_df['date']).dt.date,  # Keep only the date (first 10 characters)
    'user': base_df['owner'].apply(lambda x: x['username']),  # Extract 'name' from 'user_from'
    'coin': base_df['coin'],
    'type': base_df['type'],
    'amount': pd.to_numeric(base_df["amount"]),
    'receive': pd.to_numeric(base_df["receive"]),
})

filtered_base['price']= filtered_base["receive"]/filtered_base["amount"]

# Convert 'amount' to numeric
filtered_base['amount'] = pd.to_numeric(filtered_base['amount'])

# Precompute grouped data for the table
grouped_data = (
    filtered_base
    .assign(weighted_price=lambda df: df['price'] * df['amount'])  # Weighted price for mean calculation
    .groupby(['coin', 'date', 'type'])
    .agg(
        total_amount=('amount', 'sum'),
        mean_price=('price', lambda x: x.mean() if len(x) > 0 else 0),
        price_variance=('price', lambda x: x.var(ddof=0) if len(x) > 1 else 0)
    )
    .unstack(fill_value=0)
    .reset_index()
)

# Flatten MultiIndex columns and rename for clarity
grouped_data.columns = [
    'Coin', 'Date', 
    'Total Bought', 'Mean Price Bought', 'Price Variance Bought', 
    'Total Sold', 'Mean Price Sold', 'Price Variance Sold'
]

# Initialize the Dash app
app = Dash(__name__)

# Layout for the dashboard
app.layout = html.Div([
    html.H1(
        "Transaction Analysis Dashboard", 
        style={
            'text-align': 'center', 
            'font-family': 'Calibri',
            'background-color': '#f4f4f4', 
            'padding': '20px', 
            'margin': '0'
        }
    ),
    
    # Dropdowns and filters
    html.Div([
        html.Div([
            html.Label("Select Coin:", style={'font-family': 'Calibri'}),
            dcc.Dropdown(
                id='coin-selector',
                options=[{'label': coin, 'value': coin} for coin in filtered_base['coin'].unique()],
                value=filtered_base['coin'].unique()[0],
                multi=False,
                style={'width': '90%', 'font-family': 'Calibri'}
            ),
        ], style={'display': 'inline-block', 'width': '30%'}),
        
        html.Div([
            html.Label("Select Date:", style={'font-family': 'Calibri'}),
            dcc.Dropdown(
                id='date-selector',
                options=[{'label': str(date), 'value': str(date)} 
                         for date in filtered_base['date'].unique()],
                value=str(filtered_base['date'].unique()[0]),
                multi=False,
                style={'width': '90%', 'font-family': 'Calibri'}
            ),
        ], style={'display': 'inline-block', 'width': '30%'}),
        
        html.Div([
            html.Label("Select Type:", style={'font-family': 'Calibri'}),
            dcc.RadioItems(
                id='type-selector',
                options=[
                    {'label': 'Buy', 'value': 'buy'},
                    {'label': 'Sell', 'value': 'sell'}
                ],
                value='buy',
                inline=True,
                style={'font-family': 'Calibri'}
            ),
        ], style={'display': 'inline-block', 'width': '30%', 'padding': '10px'}),
    ], style={
        'background-color': '#f9f9f9', 
        'padding': '10px', 
        'box-shadow': '0px 4px 10px rgba(0,0,0,0.1)'
    }),
    
    # Graphs
    html.Div([
        dcc.Graph(id='transaction-graph'),
        dcc.Graph(id='price-amount-graph')
    ], style={'padding': '20px'}),
    
    # Table
    html.Div([
        html.H2("Summary Table", style={'font-family': 'Calibri', 'text-align': 'center'}),
        dash_table.DataTable(
            id='summary-table',
            columns=[
                {"name": col, "id": col} for col in grouped_data.columns
            ],
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
    ], style={'padding': '20px'}),
], style={'background-color': '#f4f4f4', 'margin': '0', 'font-family': 'Calibri'})

# Callbacks for updating the graphs and table
@app.callback(
    [Output('transaction-graph', 'figure'),
     Output('price-amount-graph', 'figure'),
     Output('summary-table', 'data')],
    [Input('coin-selector', 'value'),
     Input('date-selector', 'value'),
     Input('type-selector', 'value')]
)
def update_dashboard(selected_coin, selected_date, selected_type):
    # Filter the dataset for the graphs
    filtered_data = filtered_base[
        (filtered_base['coin'] == selected_coin) &
        (filtered_base['date'] == pd.to_datetime(selected_date)) &
        (filtered_base['type'] == selected_type)
    ]
    
    # Transaction graph (bar chart showing amounts and stock)
    fig1 = px.bar(
        filtered_data,
        x=filtered_data.index,
        y='amount',
        color='type',
        title="Transaction Amounts",
        labels={'x': 'Transaction', 'amount': 'Amount'},
    )
    
    # Create scatter chart
    scatter_chart = go.Figure()

    # Add scatter plot for price vs. amount
    scatter_chart.add_trace(
        go.Scatter(
            x=filtered_data['amount'],
            y=filtered_data['price'],
            mode='markers',
            marker=dict(size=10, color='blue', opacity=0.7),
            name='Ofertas del día'
            labels={'amount':''}
        )
    )

    # Add a point for the mean amount and mean price
    scatter_chart.add_trace(
        go.Scatter(
            x=[mean_amount],
            y=[mean_price],
            mode='markers',
            marker=dict(size=15, color='orange', symbol='star'),
            name=f'Mean Point (Amount: {mean_amount:.2f}, Price: {mean_price:.2f})'
        )
    )

    # Update layout for better visualization
    scatter_chart.update_layout(
        title=f"Scatter Chart: {coin} ({tran_type}) on {date}",
        xaxis_title="Amount",
        yaxis_title="Price",
        plot_bgcolor="white",
        xaxis=dict(gridcolor='lightgrey'),
        yaxis=dict(gridcolor='lightgrey'),
        legend=dict(title="Legend"),
    )
    
    # Filter the grouped data for the table
    filtered_table_data = grouped_data[grouped_data['Date'] == pd.to_datetime(selected_date)].to_dict('records')
    
    return fig1, fig2, filtered_table_data

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
