import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
sns.set()
    
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

    if len(dates) > 100:
        ax.set_xticks(ax.get_xticks()[::10])
    elif len(dates) > 50:
        ax.set_xticks(ax.get_xticks()[::5])
    elif len(dates) > 20 and len(dates)<= 50:
        ax.set_xticks(ax.get_xticks()[::2])

    # Show grid lines
    ax.grid(True)
    return fig      

def get_daily_spread_chart(data):
    dates = [element[0] for element in data]
    values = [abs(element[1]["ask"] - element[1]["bid"]) for element in data]
    
    # Convert datetime.date objects to matplotlib's date format
    date_list = [mdates.date2num(date) for date in dates]

    # Create plot
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Plot the data
    ax.plot(date_list, values, marker='o')

    # Format the x-axis
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
    ax.xaxis.set_major_locator(mdates.MonthLocator())

    # Set tick locations
    ax.set_xticks(date_list)

    # Rotate x-axis labels
    plt.gcf().autofmt_xdate()

    # Add title and labels
    ax.set_title('Spread diario')
    ax.set_xlabel('Fecha')
    ax.set_ylabel('Spread')

    if len(dates) > 100:
        ax.set_xticks(ax.get_xticks()[::10])
    elif len(dates) > 50:
        ax.set_xticks(ax.get_xticks()[::5])
    elif len(dates) > 20 and len(dates)<= 50:
        ax.set_xticks(ax.get_xticks()[::2])

    # Show grid lines
    ax.grid(True)
    return fig

def offer_vs_demmand(daily_spreads):
    demand_offer = [0,0]
    for element in daily_spreads:
        difference = element[1]["demand"] - element[1]["offer"]
        if difference > 0:
            demand_offer[0] += 1
        elif difference < 0:
            demand_offer[1] += 1
    return demand_offer
