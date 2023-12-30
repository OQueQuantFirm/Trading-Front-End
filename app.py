from flask import Flask, render_template, request, redirect, url_for, session, flash
import ccxt
import os
import finta
import pandas as pd
import numpy as np
from order import OrderManager
from news import CryptoNewsSentimentFetcher 
from dotenv import load_dotenv
load_dotenv()  # Load variables from .env file

app = Flask(__name__)
app.secret_key = 'trading'  # Change this to a secure secret key

api_key = os.getenv("RAPIDAPI_KEY")  # Use os.getenv to get the API key

class OHLCVAnalyzer:
    def __init__(self):
        self.exchange = ccxt.kucoinfutures({
            'apiKey': os.getenv('API_KEY'),
            'secret': os.getenv('SECRET_KEY'),
            'password': os.getenv('PASSPHRASE'),
            'enableRateLimit': True
        })

    def calculate_support_resistance_levels(self, symbol, timeframe='15m', window_size=20, bollinger_window=20, bollinger_dev=2):
        try:
            ohlcv_data = self.exchange.fetch_ohlcv(symbol, timeframe=timeframe)
            if not ohlcv_data:
                raise ValueError(f"No historical price data available for {symbol}")

            df = pd.DataFrame(ohlcv_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

            # Calculate rolling minimum and maximum closing prices
            df['rolling_min'] = df['close'].rolling(window=window_size, min_periods=1).min()
            df['rolling_max'] = df['close'].rolling(window=window_size, min_periods=1).max()

            # Calculate Bollinger Bands
            df['sma'] = finta.TA.SMA(df, period=bollinger_window)
            df['upper_band'] = df['sma'] + (bollinger_dev * df['close'].rolling(window=bollinger_window).std())
            df['lower_band'] = df['sma'] - (bollinger_dev * df['close'].rolling(window=bollinger_window).std())

            # Identify potential support and resistance levels
            support_level = df['sma'].dropna().iloc[-1]  # Use the last value of the SMA as support
            resistance_level = df['sma'].dropna().iloc[-1]  # Use the last value of the SMA as resistance

            # Print Bollinger Bands
            #print(f"Bollinger Bands for {symbol}:\n{df[['timestamp', 'close', 'upper_band', 'lower_band']]}")

            # Print support and resistance levels
            #print(f"Support Level for {symbol}: {support_level}")
            #print(f"Resistance Level for {symbol}: {resistance_level}")

            return support_level, resistance_level

        except Exception as e:
            print(f"Error calculating support and resistance levels for {symbol}: {e}")
            return None, None

    def fetch_and_analyze_symbols(self, timeframe='15m'):
        results = []
        try:
            symbols = self.exchange.load_markets().keys()

            for symbol in symbols:
                ohlcv_data = self.exchange.fetch_ohlcv(symbol, timeframe=timeframe)
                ticker = self.exchange.fetch_ticker(symbol)  # Fetch ticker information

                if ohlcv_data:
                    df = pd.DataFrame(ohlcv_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                    df['rsi'] = finta.TA.RSI(df, period=14)
                    latest_rsi = df['rsi'].iloc[-1]

                    support_levels, resistance_levels = self.calculate_support_resistance_levels(symbol, timeframe)
                    
                    if latest_rsi > 74 or latest_rsi < 26:
                        order_book = self.fetch_order_book(symbol)
                        imbalance_percentage = self.calculate_order_book_imbalance(order_book)
                        current_price = ticker['last']  # Get the last traded price
                        # Add RSI to the dictionary
                        results.append({
                            'symbol': symbol,
                            'latest_rsi': latest_rsi,
                            'order_book_imbalance': imbalance_percentage,
                            'current_price': current_price,
                            'support_levels': support_levels,
                            'resistance_levels': resistance_levels,
                            'rsi_values': df['rsi'].tolist()  # Add RSI values to the result
                        })

        except Exception as e:
            print(f"Error fetching and analyzing symbols: {e}")

        return results

    def fetch_order_book(self, symbol, limit=100):
        try:
            order_book = self.exchange.fetch_order_book(symbol, limit=limit)
            return order_book
        except Exception as e:
            print(f"Error fetching order book data for {symbol}: {e}")
            return None

    def calculate_order_book_imbalance(self, order_book):
        try:
            if not order_book:
                raise ValueError("No order book data available for analysis.")

            bids = order_book.get('bids', [])
            asks = order_book.get('asks', [])

            total_bids = sum(bid[1] for bid in bids)
            total_asks = sum(ask[1] for ask in asks)

            if total_bids != 0 or total_asks != 0:
                imbalance = (total_bids - total_asks) / (total_bids + total_asks)
            else:
                imbalance = 0

            imbalance_percentage = imbalance * 100

            print(f"Order Book Imbalance: {imbalance_percentage}%")

            return imbalance_percentage

        except Exception as e:
            print(f"Error calculating order book imbalance: {e}")
            return None
        

def store_credentials(api_key, secret_key, passphrase):
    # Validate and store the credentials securely
    if api_key and secret_key and passphrase:
        os.environ['API_KEY'] = api_key
        os.environ['SECRET_KEY'] = secret_key
        os.environ['PASSPHRASE'] = passphrase
        return True
    return False

@app.route('/')
def index():
    # Check if the user is authenticated
    if not is_authenticated(request):
        return redirect(url_for('login'))

    timeframe = request.args.get('timeframe', '15m')
    analyzer = OHLCVAnalyzer()
    results = analyzer.fetch_and_analyze_symbols(timeframe=timeframe)
    
    # Example usage of CryptoNewsSentimentFetcher
    news_fetcher = CryptoNewsSentimentFetcher()
    news_sentiment_data = news_fetcher.fetch_news_sentiment(source="coindesk")
    
    print(f"News Sentiment Data: {news_sentiment_data}")

    return render_template('index.html', results=results, selected_timeframe=timeframe, news_sentiment=news_sentiment_data)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Retrieve API key, secret, and passphrase from the form
        api_key = request.form.get('api_key')
        secret_key = request.form.get('secret_key')
        passphrase = request.form.get('passphrase')

        # Validate and store credentials
        if store_credentials(api_key, secret_key, passphrase):
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials. Please try again.', 'danger')

    return render_template('login.html')

def is_authenticated(request):
    # Check if the user is authenticated based on your criteria
    # For example, you might check if the API key, secret, and passphrase are set
    return 'API_KEY' in os.environ and 'SECRET_KEY' in os.environ and 'PASSPHRASE' in os.environ

@app.route('/configure', methods=['GET', 'POST'])
def configure():
    # Check if the user is authenticated
    if not is_authenticated(request):
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Retrieve user-specific configuration parameters from the form
        # You can add more parameters based on your requirements
        leverage = request.form.get('leverage')
        time_in_force = request.form.get('time_in_force')
        stop_loss_percentage = float(request.form.get('stop_loss_percentage', 0.0))
        take_profit_percentage = float(request.form.get('take_profit_percentage', 0.0))
        
        # Additional order-related settings
        default_order_type = request.form.get('default_order_type')
        default_order_quantity = float(request.form.get('default_order_quantity', 0.0))
        # Add more order-related settings as needed

        # Store the configuration securely (e.g., in a database or in-memory storage)
        # For simplicity, we'll store them in the session for now
        session['leverage'] = leverage
        session['time_in_force'] = time_in_force
        session['stop_loss_percentage'] = stop_loss_percentage
        session['take_profit_percentage'] = take_profit_percentage
        session['default_order_type'] = default_order_type
        session['default_order_quantity'] = default_order_quantity
        # Store more order-related settings in the session

        # Print the configured values for demonstration purposes
        print(f"Leverage: {leverage}")
        print(f"Time in Force: {time_in_force}")
        print(f"Stop Loss Percentage: {stop_loss_percentage}%")
        print(f"Take Profit Percentage: {take_profit_percentage}")
        print(f"Default Order Type: {default_order_type}")
        print(f"Default Order Quantity: {default_order_quantity}")

    return render_template('configure.html')


@app.route('/place_order', methods=['POST'])
def place_order():
    if not is_authenticated(request):
        return redirect(url_for('login'))

    symbol = request.form.get('symbol')
    side = request.form.get('side')
    amount = float(request.form.get('amount'))
    leverage = request.form.get('leverage')
    trigger_price = float(request.form.get('trigger_price'))
    stop_loss_price = float(request.form.get('stop_loss_price'))
    take_profit_price = float(request.form.get('take_profit_price'))
    post_only = request.form.get('post_only')
    
    # New field to determine the order type (market or limit)
    order_type = request.form.get('order_type')  # Add this field to the form in the HTML

    # Replace 'your_api_key' and 'your_api_secret' with your actual API key and secret
    exchange = ccxt.kucoinfutures({
        'apiKey': 'your_api_key',
        'secret': 'your_api_secret',
        'enableRateLimit': True,
    })

    order_manager = OrderManager(exchange, symbol)

    if order_type == 'market':
        # Example: Create a market order
        result = order_manager.create_market_order(side, amount, post_only)
    elif order_type == 'limit':
        # Example: Create a limit order
        result = order_manager.create_limit_order(side, amount, trigger_price, post_only)

    print(result)

    # Example: Create a stop-loss order
    result = order_manager.create_stop_loss_order(side, amount, trigger_price, stop_loss_price, post_only)
    print(result)

    # Add other order types as needed

    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)