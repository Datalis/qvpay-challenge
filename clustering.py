import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score


def preprocess_data(df):

    for col in ['Amount', 'Receive', 'Average Rating']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    df = df.dropna(subset=['Amount', 'Receive', 'Average Rating'])

    key_columns = ['User UUID', 'Username', 'Name', 'Lastname']
    df_keys = df[key_columns].drop_duplicates(subset=['Username'])

    user_stats = df.groupby('Username').agg(
        Total_Transactions=('Transaction UUID', 'count'),
        Total_Volume=('Amount', 'sum'),
        Coins_Traded=('Coin', 'nunique'),
        Avg_Rating=('Average Rating', 'mean')
    ).reset_index()

    if not user_stats['Username'].is_unique:
        raise ValueError("La columna 'Username' en user_stats no es única después de agrupar.")

    scaler = StandardScaler()
    features = ['Total_Transactions', 'Total_Volume', 'Coins_Traded', 'Avg_Rating']
    scaled_data = scaler.fit_transform(user_stats[features])

    scaled_df = pd.DataFrame(scaled_data, columns=features)

    result_df = pd.merge(user_stats, df_keys, on='Username', how='left')

    return scaled_df, result_df

def perform_kmeans(df, n_clusters, max_iter=300, tol=1e-4):

    kmeans = KMeans(n_clusters=n_clusters, init='k-means++', n_init=10, max_iter=max_iter, tol=tol, random_state=42)
    labels = kmeans.fit_predict(df)

    # Métricas de evaluación
    inertia = kmeans.inertia_
    silhouette = silhouette_score(df, labels)
    calinski_harabasz = calinski_harabasz_score(df, labels)
    davies_bouldin = davies_bouldin_score(df, labels)

    print(f"Inercia: {inertia:.4f}")
    print(f"Silhouette Score: {silhouette:.4f}")
    print(f"Calinski-Harabasz Score: {calinski_harabasz:.4f}")
    print(f"Davies-Bouldin Score: {davies_bouldin:.4f}")

    return {
        "model": kmeans,
        "labels": labels,
        "metrics": {
            "inertia": inertia,
            "silhouette_score": silhouette,
            "calinski_harabasz_score": calinski_harabasz,
            "davies_bouldin_score": davies_bouldin
        }
    }


def get_cluster_centroids_original_scale(kmeans_model, scaler, feature_names):
    centroids_scaled = kmeans_model.cluster_centers_
    centroids_original = scaler.inverse_transform(centroids_scaled)
    return pd.DataFrame(centroids_original, columns=feature_names)


def add_cluster_labels_to_df(original_df, processed_df, labels, scaler):
    original_scaled = pd.DataFrame(scaler.inverse_transform(processed_df), columns=processed_df.columns)
    original_scaled['cluster_label'] = labels
    return original_scaled


def plot_clusters(user_stats, x_col, y_col, cluster_col, title="Clustering Visualization"):
    unique_clusters = user_stats[cluster_col].unique()
    palette = sns.color_palette("tab10", len(unique_clusters))

    # Crear figura y ejes
    fig, ax = plt.subplots(figsize=(8, 6))
    for i, cluster in enumerate(unique_clusters):
        cluster_data = user_stats[user_stats[cluster_col] == cluster]
        ax.scatter(
            cluster_data[x_col],
            cluster_data[y_col],
            color=palette[i],
            label=f'Cluster {cluster}',
            s=100,
            alpha=0.7
        )

    # Configurar etiquetas y leyenda
    ax.legend(title="Clusters")
    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    ax.set_title(title)
    ax.grid(True)

    # Devolver figura
    return fig

def get_cluster_members(df_with_labels, cluster_label):

    cluster_members = df_with_labels[df_with_labels['cluster_label'] == cluster_label]

    selected_columns = ['User UUID', 'Username', 'Name', 'Lastname']
    return cluster_members[selected_columns]
