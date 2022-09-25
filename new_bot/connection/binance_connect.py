from decimal import Decimal
from typing import Dict

from binance.spot import Spot as Client

from schemas import TradeStatus

from settings import KEY
from settings import SECRET


# client = Client(base_url="https://testnet.binance.vision", key=KEY, secret=SECRET)
client = Client(key=KEY, secret=SECRET)


def trade_market(coin: str, side: TradeStatus, amount: float) -> Dict:
    symbol = f"{coin}USDT"
    type_trade = "MARKET"
    # quantity = 0.002
    quantity = amount
    return client.new_order(symbol, side, type_trade, quantity=quantity)


def trade_limit(coin: str, side: TradeStatus, amount: float, sell_price: float) -> Dict:
    symbol = f"{coin}USDT"
    type_trade = "LIMIT"
    # quantity = 0.002
    quantity = amount
    price = sell_price
    return client.new_order(symbol, side, type_trade, quantity=quantity, price=price, timeInForce="GTC")


def get_price_now(coin: str) -> Decimal:
    symbol = f"{coin}USDT"
    prices = client.ticker_price(symbol=symbol)
    return Decimal(prices['price'])
