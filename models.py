import dateutil.parser
import datetime

class Balance:
    def __init__(self, info):
        self.initial_margin = float(info["initialMargin"])
        self.maintenance_margin = float(info["maintMargin"])
        self.margin_balance = float(info["marginBalance"])
        self.wallet_balance = float(info["walletBalance"])
        self.unrealized_pnl = float(info["unrealizedProfit"])

class Candle:
    def __init__(self, candle_info):
        self.timestamp = candle_info[0]
        self.open = float(candle_info[1])
        self.close = float(candle_info[2])
        self.high = float(candle_info[3])
        self.low = float(candle_info[4])
        self.volume = float(candle_info[5])

def tick_to_decimals(tick_size: float) -> int:
    tick_size_str = "{0:.8f}".format(tick_size)
    while tick_size_str[-1] == "0":
        tick_size_str = tick_size_str[:-1]

    split_tick = tick_size_str.split(".")

    if len(split_tick) > 1:
        return len(split_tick[1])
    else:
        return 0

class Contract:
    def __init__(self, contract_info):
        self.symbol = contract_info['symbol']
        self.base_asset = contract_info['baseAsset']
        self.quote_asset = contract_info['quoteAsset']
        self.price_decimals = contract_info['pricePrecision']
        self.quantity_decimals = contract_info['quantityPrecision']
        self.tick_size = 1 / pow(10, contract_info['pricePrecision'])
        self.lot_size = 1 / pow(10, contract_info['quantityPrecision'])

class OrderStatus:
    def __init__(self, order_info):
        self.order_id = order_info['orderId']
        self.status = order_info['status']
        self.avg_price = float(order_info['avgPrice'])
