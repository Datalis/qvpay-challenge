import requests
import pandas as pd
import matplotlib.pyplot as plt

from utils import TOKEN, API_URL
from clustering import preprocess_data, perform_kmeans, get_cluster_members, plot_clusters


def get_data_p2p(token, api_url="https://qvapay.com/api/p2p"):
    all_data = [] 
    current_url = api_url

    while current_url:
        try:
            response = requests.get(current_url, headers={'Accept': 'application/json'})
            response.raise_for_status()
            data = response.json()

            if 'data' in data:
                all_data.extend(data['data'])

            current_url = data.get('next_page_url')

        except requests.exceptions.RequestException as e:
            raise Exception(f"Error al conectar con la API: {e}")
        except Exception as e:
            raise Exception(f"Error inesperado: {e}")

    return all_data

def turn_data_into_df(data):
    transactions = []
    for transaction in data:
        transactions.append({
            'Transaction UUID': transaction.get('uuid'),
            'Type': transaction.get('type'),
            'Coin': transaction.get('coin'),
            'Amount': transaction.get('amount'),
            'Receive': transaction.get('receive'),
            'Message': transaction.get('message'),
            'Status': transaction.get('status'),
            'Created At': transaction.get('created_at'),
            'Updated At': transaction.get('updated_at'),
            'Coin Name': transaction.get('coin_data', {}).get('name', None), 
            'Coin Price': transaction.get('coin_data', {}).get('price', None), 
            'User UUID': transaction.get('owner', {}).get('uuid', None), 
            'Username': transaction.get('owner', {}).get('username', None),
            'Name': transaction.get('owner', {}).get('name', None),
            'Lastname': transaction.get('owner', {}).get('lastname', None),
            'KYC': transaction.get('owner', {}).get('kyc', None),
            'Average Rating': transaction.get('owner', {}).get('average_rating', None),
        })

    df = pd.DataFrame(transactions)
    return df

def plot_daily_spread(market_makers, coin):
    coin_data = market_makers[market_makers['Coin'] == coin]

    if coin_data.empty:
        print(f"No se encontraron transacciones de Market Makers para la moneda {coin}.")
        return None

    print(f"Transacciones de Market Makers para {coin}: {coin_data.shape[0]}")

    coin_data = coin_data.copy()
    coin_data['Created At'] = pd.to_datetime(coin_data['Created At'], errors='coerce')

    coin_data = coin_data.dropna(subset=['Created At', 'Coin Price'])

    coin_data['Coin Price'] = coin_data['Coin Price'].astype(str)
    coin_data['Coin Price'] = coin_data['Coin Price'].str.replace(r'[^0-9.]', '', regex=True)
    coin_data['Coin Price'] = pd.to_numeric(coin_data['Coin Price'], errors='coerce')

    coin_data = coin_data.dropna(subset=['Coin Price'])

    coin_data['Type'] = coin_data['Type'].str.strip().str.lower()

    market_maker_ids = coin_data['User UUID'].unique()

    fig, ax = plt.subplots(figsize=(12, 8))

    for market_maker in market_maker_ids:
        mm_data = coin_data[coin_data['User UUID'] == market_maker]

        username = mm_data['Username'].iloc[0] if not mm_data['Username'].empty else f"UUID {market_maker}"

        daily_sell = mm_data[mm_data['Type'] == 'sell'].groupby(mm_data['Created At'].dt.date)['Coin Price'].mean()
        daily_buy = mm_data[mm_data['Type'] == 'buy'].groupby(mm_data['Created At'].dt.date)['Coin Price'].mean()

        all_dates = pd.date_range(start=coin_data['Created At'].min(), end=coin_data['Created At'].max())
        daily_sell = daily_sell.reindex(all_dates, fill_value=0)
        daily_buy = daily_buy.reindex(all_dates, fill_value=0)

        daily_spread = daily_sell - daily_buy

        if not daily_spread.empty:
            ax.plot(
                daily_spread.index, 
                daily_spread.values, 
                marker='o', 
                label=f'Market Maker: {username}'
            )

    ax.set_xlabel('Fecha')
    ax.set_ylabel('Spread Promedio')
    ax.set_title(f'Promedio Diario del Spread por Market Maker para {coin}')
    ax.legend(title="Market Makers", loc='best', bbox_to_anchor=(1, 1))
    ax.grid()

    return fig

import matplotlib.pyplot as plt
import pandas as pd

import pandas as pd
import matplotlib.pyplot as plt

def analyze_volume(df, coin):
    coin_data = df[df['Coin'] == coin]

    if coin_data.empty:
        print(f"No se encontraron transacciones para la moneda {coin}.")
        return None

    # Asegurarse de que la columna 'Amount' sea numérica
    coin_data['Amount'] = pd.to_numeric(coin_data['Amount'], errors='coerce')

    coin_data['Created At'] = pd.to_datetime(coin_data['Created At'])

    daily_offer = coin_data[coin_data['Type'] == 'sell'].groupby(coin_data['Created At'].dt.date)['Amount'].sum()
    daily_demand = coin_data[coin_data['Type'] == 'buy'].groupby(coin_data['Created At'].dt.date)['Amount'].sum()

    # Crear el DataFrame asegurándose de que los valores sean numéricos
    volume_comparison = pd.DataFrame({
        'Oferta': daily_offer,
        'Demanda': daily_demand
    }).fillna(0)

    # Convertir las columnas a numéricas si no lo están
    volume_comparison['Oferta'] = pd.to_numeric(volume_comparison['Oferta'], errors='coerce')
    volume_comparison['Demanda'] = pd.to_numeric(volume_comparison['Demanda'], errors='coerce')

    # Crear figura y ejes
    fig, ax = plt.subplots(figsize=(16, 8))  
    
    # Cambiar colores de las barras
    volume_comparison.plot(kind='bar', ax=ax, width=0.8, color=['red', 'green'])
    
    ax.set_title(f'Volumen Diario de Oferta y Demanda para {coin}', fontsize=16)
    ax.set_xlabel('Fecha', fontsize=12)
    ax.set_ylabel('Volumen', fontsize=12)

    # Reducir el número de etiquetas en el eje X
    num_ticks = 10  # Muestra solo 10 etiquetas en el eje X
    ax.set_xticks(range(0, len(volume_comparison), max(1, len(volume_comparison) // num_ticks)))
    ax.set_xticklabels(volume_comparison.index[::max(1, len(volume_comparison) // num_ticks)], rotation=45, fontsize=10)

    plt.tight_layout()  # Asegurarse de que todo se ajuste en la figura

    return fig

def data_clustization(df, n_clusters=4, plot=True):
    scaled_df, result_df = preprocess_data(df)

    results = perform_kmeans(scaled_df, n_clusters=n_clusters)

    result_df['cluster_label'] = results['labels']


    if plot:
        plot_clusters(result_df, 'Total_Transactions', 'Total_Volume', 'cluster_label')

    return result_df

def identify_market_makers(df, result_df, cluster_label=-1):
    if cluster_label == -1:
        # Heurística: Seleccionar el cluster con el mayor centroide en Total_Transactions y Total_Volume
        cluster_centers = result_df.groupby('cluster_label')[['Total_Transactions', 'Total_Volume']].mean()
        cluster_label = cluster_centers.sum(axis=1).idxmax()
        print("entree")

    print(f"Cluster seleccionado: {cluster_label}")
    cluster_members = result_df[result_df['cluster_label'] == cluster_label]

    print(cluster_members[['User UUID', 'Username', 'Name', 'Lastname']])

    market_makers = df[df['Username'].isin(cluster_members['Username'])]

    return market_makers

def main():

    data = get_data_p2p()
    print(data)

    df = turn_data_into_df(data)
    
    result_df = data_clustization(df, n_clusters=4, plot=True)

    market_makers = identify_market_makers(df, result_df)

    print(market_makers.head())

    plot_daily_spread(market_makers, 'BANK_MLC')
    
    analyze_volume(df, 'BANK_MLC')

if __name__ == "__main__":
    main()
