from binance.spot import Spot as Client

from schemas import TradeStatus

from settings import KEY
from settings import SECRET


# client = Client(base_url="https://testnet.binance.vision", key=KEY, secret=SECRET)
client = Client(key=KEY, secret=SECRET)


def trade_market(coin: str, side: TradeStatus, amount: float):
    symbol = f"{coin}USDT"
    type_trade = "MARKET"
    # quantity = 0.002
    quantity = amount
    return client.new_order(symbol, side, type_trade, quantity=quantity)
