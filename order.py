import ccxt

class OrderManager:
    def __init__(self, exchange, symbol):
        self.exchange = exchange
        self.symbol = symbol

    def create_order(self, order_type, side, amount, trigger_price=None, stop_loss_price=None, take_profit_price=None, post_only=None):
        try:
            order_params = {
                'symbol': self.symbol,
                'type': order_type,
                'side': side,
                'quantity': amount,
                'postOnly': post_only,
                # Add other parameters as needed
            }

            if order_type == 'LIMIT':
                order_params['price'] = trigger_price

            if order_type == 'STOP_MARKET':
                order_params['stopPrice'] = stop_loss_price

            if order_type == 'TAKE_PROFIT_MARKET':
                order_params['stopPrice'] = take_profit_price

            result = self.exchange.create_order(**order_params)
            return result

        except ccxt.ExchangeError as e:
            print(f"Error creating order: {e}")
            return None

    def create_market_order(self, side, amount, post_only=None):
        return self.create_order('MARKET', side, amount, post_only=post_only)

    def create_limit_order(self, side, amount, trigger_price, post_only=None):
        return self.create_order('LIMIT', side, amount, trigger_price=trigger_price, post_only=post_only)

    def create_stop_loss_order(self, side, amount, trigger_price, stop_loss_price, post_only=None):
        return self.create_order('STOP_MARKET', side, amount, trigger_price=trigger_price, stop_loss_price=stop_loss_price, post_only=post_only)

    def create_take_profit_order(self, side, amount, trigger_price, take_profit_price, post_only=None):
        return self.create_order('TAKE_PROFIT_MARKET', side, amount, trigger_price=trigger_price, take_profit_price=take_profit_price, post_only=post_only)
