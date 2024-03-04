import os
import json
import requests
from colorama import Fore, Style
from candlestick_chart import Candle, Chart
import inquirer
from datetime import datetime, timedelta
import asciichartpy

API_KEY_FILE = "secret/api_key.json"
STOCK_LIST_FILE = "secret/stocks.json"
STOCK_DATA_DIR = "stock_data"

# Function to clear the screen


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

# Load API key from file


def load_api_key():
    if os.path.exists(API_KEY_FILE):
        with open(API_KEY_FILE, "r") as f:
            return json.load(f)
    else:
        return None

# Save API key to file


def save_api_key(api_key):
    with open(API_KEY_FILE, "w") as f:
        json.dump(api_key, f)

# Load stock list from file


def load_stock_list():
    if os.path.exists(STOCK_LIST_FILE):
        with open(STOCK_LIST_FILE, "r") as f:
            return json.load(f)
    else:
        return []

# Save stock list to file


def save_stock_list(stock_list):
    with open(STOCK_LIST_FILE, "w") as f:
        json.dump(stock_list, f)

# Load stock data from file


def load_stock_data(symbol):
    file_path = os.path.join(STOCK_DATA_DIR, f"{symbol}.json")
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return json.load(f)
    else:
        return None

# Save stock data to file


def save_stock_data(symbol, data):
    if not os.path.exists(STOCK_DATA_DIR):
        os.makedirs(STOCK_DATA_DIR)
    file_path = os.path.join(STOCK_DATA_DIR, f"{symbol}.json")
    with open(file_path, "w") as f:
        json.dump(data, f)

# Check if stock data is stale (older than 5 minutes)


def is_stock_data_stale(symbol):
    file_path = os.path.join(STOCK_DATA_DIR, f"{symbol}.json")
    if os.path.exists(file_path):
        modification_time = datetime.fromtimestamp(os.path.getmtime(file_path))
        return (datetime.now() - modification_time) > timedelta(minutes=5)
    return True

# Set API key


def set_api_key():
    api_key = input("Enter your API key: ")
    save_api_key(api_key)
    print(Fore.GREEN + "API key saved successfully.")

# Get stock data from Alpha Vantage API


def get_stock_data(symbol):
    if not is_stock_data_stale(symbol):
        # Load data from file if not stale
        return load_stock_data(symbol)

    api_key = load_api_key()
    if api_key is None:
        print(Fore.RED + "API key is not set. Please set the API key first.")
        return None

    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={symbol}&interval=5min&apikey={api_key}'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        # Save data to file
        save_stock_data(symbol, data)
        return data
    else:
        print(
            Fore.RED + f"Failed to fetch data for {symbol}. Error {response.status_code}.")
        return None

# Add stock to the list


def add_stock(symbol):
    stock_list = load_stock_list()
    if symbol not in stock_list:
        stock_list.append(symbol)
        save_stock_list(stock_list)
        print(Fore.GREEN + f"Stock {symbol} added successfully.")
    else:
        print(Fore.YELLOW + f"Stock {symbol} is already in the list.")

# Remove stock from the list


def remove_stock(symbol):
    stock_list = load_stock_list()
    if symbol in stock_list:
        stock_list.remove(symbol)
        save_stock_list(stock_list)
        print(Fore.GREEN + f"Stock {symbol} removed successfully.")
    else:
        print(Fore.YELLOW + f"Stock {symbol} is not in the list.")

# Show stock information


def show_stock_info():
    stock_list = load_stock_list()
    if not stock_list:
        print(Fore.YELLOW + "No stock symbols found. Please add stocks.")
        return

    questions = [
        inquirer.List('symbol',
                      message='Select a stock symbol:',
                      choices=stock_list,
                      ),
    ]
    answer = inquirer.prompt(questions)
    symbol = answer['symbol']
    stock_data = get_stock_data(symbol)
    if stock_data is not None and 'Meta Data' in stock_data:
        meta_data = stock_data['Meta Data']
        print(Fore.CYAN + f"Stock Symbol: {meta_data['2. Symbol']}")
        print(f"Last Refreshed: {meta_data['3. Last Refreshed']}")
        print(f"Interval: {meta_data['4. Interval']}")
        print(f"Output Size: {meta_data['5. Output Size']}")
        print(f"Time Zone: {meta_data['6. Time Zone']}")
    else:
        print(Fore.RED + "Failed to fetch stock information.")

# Function to calculate moving averages


def calculate_moving_average(data, window_size):
    moving_averages = []
    for i in range(len(data) - window_size + 1):
        window = data[i:i+window_size]
        average = sum(window) / window_size
        moving_averages.append(average)
    return moving_averages

# Add moving averages to chart
def add_moving_averages_chart(closes):
    window_sizes = [20, 50]
    for window_size in window_sizes:
        moving_averages = calculate_moving_average(closes, window_size)
        print(Fore.CYAN + f"Moving Average ({window_size}):")
        print(asciichartpy.plot(moving_averages, {'height': 5}))

# Plot stock chart
def plot_stock_chart():
    stock_list = load_stock_list()
    if not stock_list:
        print(Fore.YELLOW + "No stock symbols found. Please add stocks.")
        return

    questions = [
        inquirer.List('symbol',
                      message='Select a stock symbol:',
                      choices=stock_list,
                      ),
    ]
    answer = inquirer.prompt(questions)
    symbol = answer['symbol']
    stock_data = get_stock_data(symbol)
    if stock_data is not None and 'Time Series (5min)' in stock_data:
        candles = []
        close_prices = []  # List to store close prices for moving averages
        for key, value in stock_data['Time Series (5min)'].items():
            open_price = float(value['1. open'])
            high_price = float(value['2. high'])
            low_price = float(value['3. low'])
            close_price = float(value['4. close'])
            candle = Candle(open=open_price, close=close_price,
                            high=high_price, low=low_price)
            candles.append(candle)
            close_prices.append(close_price)

        chart = Chart(candles, title=f"Candlestick Chart for {symbol}")
        chart.set_name(symbol)

        new_width = 150
        new_height = 25
        chart.update_size(new_width, new_height)

        # Draw chart
        chart.draw()

        # Add moving averages
        add_moving_averages_chart(close_prices)

    else:
        print(Fore.RED + "Failed to fetch stock data.")

# View news for a stock


def view_stock_news():
    stock_list = load_stock_list()
    if not stock_list:
        print(Fore.YELLOW + "No stock symbols found. Please add stocks.")
        return

    questions = [
        inquirer.List('symbol',
                      message='Select a stock symbol:',
                      choices=stock_list,
                      ),
    ]

    answer = inquirer.prompt(questions)
    symbol = answer['symbol']
    news_data = get_stock_news(symbol)
    if news_data is not None and 'feed' in news_data:
        articles = news_data['feed']
        print(Fore.CYAN + "Stock News:")
        for article in articles:
            print(Fore.YELLOW + "Title:", article['title'])
            print(Fore.GREEN + "Source:", article['source'])
            print(Fore.BLUE + "Published At:", article['time_published'])
            print(Fore.MAGENTA + "Summary:", article['summary'])
            print()
    else:
        print(Fore.RED + "Failed to fetch stock news.")

# Main menu


def main_menu():
    questions = [
        inquirer.List('action',
                      message='What would you like to do?',
                      choices=[
                          'Set API Key',
                          'Add Stock',
                          'Remove Stock',
                          'Show Stock Information',
                          'Plot Stock Chart',
                          'View Stock News',
                          'Exit'
                      ],
                      ),
    ]
    answer = inquirer.prompt(questions)
    return answer['action']

# Main function


def main():
    while True:
        choice = main_menu()

        if choice == 'Set API Key':
            set_api_key()
            clear_screen()
        elif choice == 'Add Stock':
            symbol = input("Enter stock symbol to add: ")
            clear_screen()
            add_stock(symbol)
        elif choice == 'Remove Stock':
            symbol = input("Enter stock symbol to remove: ")
            clear_screen()
            remove_stock(symbol)
        elif choice == 'Show Stock Information':
            clear_screen()
            show_stock_info()
        elif choice == 'Plot Stock Chart':
            clear_screen()
            plot_stock_chart()
        elif choice == 'View Stock News':
            clear_screen()
            view_stock_news()
        elif choice == 'Exit':
            print(Fore.YELLOW + "Exiting the program.")
            break
        else:
            print(Fore.RED + "Invalid choice. Please enter a valid option.")


# Entry point of the program
if __name__ == "__main__":
    main()
