import matplotlib.pyplot as plt
import matplotlib.dates as mdates
    
def get_date_chart(data):
    # Create plot
    fig, ax = plt.subplots(figsize=(12, 6))
    dates = [element[0] for element in data]
    values = [abs(element[1]["ask"] - element[1]["bid"]) for element in data]

    ax.plot_date(dates, values)

    # Customize x-axis
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
    ax.xaxis.set_major_locator(mdates.MonthLocator())

    # Rotate x-axis labels
    plt.gcf().autofmt_xdate()

    # Add title and labels
    ax.set_title('Spread diario')
    ax.set_xlabel('Fecha')
    ax.set_ylabel('Spread')

    # Show grid lines
    ax.grid(True)
    return fig      