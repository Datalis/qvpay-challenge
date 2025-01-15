import matplotlib.pyplot as plt

def process_dates(data):
    for date, spread in data:
        if spread["ask"] == None or spread["bid"]== None:
            del data[date]
        else:
            data[date]
    
def get_date_chart(data):
    # Configuramos el eje X para que acepte fechas
    plt.gca().xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%Y-%m-%d'))

    # Creamos el gráfico
    fig = plt.figure(figsize=(10, 6))
    for i in range(len(data)):
        plt.plot(data[0], data[1], 'bo-')

    # Configuramos los ejes y título
    plt.xlabel('Fecha')
    plt.ylabel('Valor')
    plt.title('Gráfico con fechas en el eje X')

    # Formateamos las fechas del eje X
    plt.gcf().autofmt_xdate()

    return fig