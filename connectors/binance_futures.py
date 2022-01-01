import logging
import requests
import time
import hmac
import hashlib
import websocket
import json
import threading
import ssl
import typing
import collections

from urllib.parse import urlencode
from models import  *

"https://fapi.binance.com"
"https://testnet.binancefuture.com" # account data

"wss://fstream.binance.com" # live data

logger = logging.getLogger()

class BinanceFutureClient:
    def __init__(self, public_key:str ,secret_key:str , testnet:bool):
        if testnet:
            self._base_url = "https://testnet.binancefuture.com"
            self._wss_url = "wss://stream.binancefuture.com/ws"
        else:
            self._base_url = "https://fapi.binance.com"
            self._wss_url = "wss://fstream.binance.com/ws"

        self._public_key = public_key
        self._secret_key = secret_key

        self._headers = {'X-MBX-APIKEY': self._public_key}

        self.contracts = self.get_contracts()
        self.balances = self.get_balances()

        self.prices = dict()
        self.logs = []

        self._ws_id = 1
        self._ws = None

        t = threading.Thread(target=self._start_ws)

        t.start()

        logger.info("Binance Futuers")

    def _add_log(self, msg: str):
        logger.infor("%s", msg)
        self.logs.append({"log": msg, "displayed": False})

    def _generate_signature(self, data: typing.Dict) -> str:
        return hmac.new(self._secret_key.encode(), urlencode(data).encode(), hashlib.sha256).hexdigest()

    def _make_requests(self, method: str, endpoint: str, data: typing.Dict):
        if method == "GET":
            try:
                response = requests.get(self._base_url + endpoint, params=data)
            except Exception as e:
                logger.error("Connection error while making %s request to %s", method, endpoint, e)
                return None
        elif method == "POST":
            try:
                response = requests.post(self._base_url + endpoint, params=data)
            except Exception as e:
                logger.error("Connection error while making %s request to %s", method, endpoint, e)
                return None
        elif method == "DELETE":
            try:
                response = requests.delete(self._base_url + endpoint, params=data)
            except Exception as e:
                logger.error("Connection error while making %s request to %s", method, endpoint, e)
                return None
        else:
            return ValueError()

        if response.status_code == 200:
            return response.json()
        else:
            logger.error("Error while making %s request to %s: %s (error code %s)",
                         method, endpoint, response.json(), response.status_code)
            return None

    def get_contracts(self) -> typing.Dict[str, Contract]:
        exchange_info = self._make_requests("GET", "/fapi/v1/exchangeInfo", dict())

        contracts = dict()

        if exchange_info:
            for contract_data in exchange_info["symbols"]:
                contracts[contract_data["pair"]] = Contract(contract_data)

        return collections.OrderedDict(sorted(contracts.items()))

    def get_historical_candles(self, contract: Contract, interval: str) -> typing.List[Candle]:
        data = dict()
        data['symbol'] = contract.symbol
        data['interval'] = interval
        data['limit'] = 1000

        raw_candles = self._make_requests("GET","/fapi/v1/klines", data)
        candles = []
        if raw_candles is not None:
            for c in raw_candles:
                candles.append(Candle(c))

        return candles

    def get_bid_ask(self,contract: Contract) -> typing.Dict[str, float]:
        data = dict()
        data['symbol'] = contract.symbol
        ob_data = self._make_requests("GET", "/fapi/v1/ticker/bookTicker",data)

        if ob_data:
            if contract.symbol not in self.prices:
                self.prices[contract.symbol] = {'bid': float(ob_data["bidPrice"]), 'ask': float(ob_data["askPrice"])}
            else:
                self.prices[contract.symbol]['bid'] = float(ob_data["bidPrice"])
                self.prices[contract.symbol]['ask'] = float(ob_data["askPrice"])

            return self.prices[contract.symbol]

    def get_balances(self) -> typing.Dict[str, Balance]:
        data = dict()
        data["timestamp"] = int(time.time() * 1000)
        data['signature'] = self._generate_signature(data)


        balances = dict()
        account_data = self._make_requests("GET", "/fapi/v2/account", data=data)

        if account_data:
            for a in account_data["assets"]:
                balances[a["assets"]] = Balance(a)


        # print(balances['USDT'].wallet_balance)
        return balances

    def place_order(self, contract: Contract, side: str, quantity: float, order_type: str, price=None, tif=None) -> OrderStatus:
        data = dict()
        data['symbol'] = contract.symbol
        data['side'] = side
        data['quantity'] = quantity
        data['type'] = order_type

        if price:
            data['price'] = price

        if tif:
            data['timeInForce'] = tif

        data['timestamp'] = int(time.time() * 1000)
        data['signature'] = self._generate_signature(data)

        order_status  = self._make_requests("POST", "/fapi/v1/order", data)

        if order_status:
            order_status = OrderStatus(order_status)

        return order_status

    def cancel_order(self, contract: Contract, order_id: int) -> OrderStatus:
        data = dict()
        data['orderId'] =  order_id
        data['symbol'] = contract.symbol

        data['timestamp'] = int(time.time() * 1000)
        data['signature'] = self._generate_signature(data)

        order_status = self._make_requests("DELETE","/fapi/v1/order", data)

        if order_status:
            order_status = OrderStatus(order_status)

        return order_status

    def get_order_status(self, contract: Contract, order_id: int) -> OrderStatus:
        data = dict()
        data["timestamp"] = int(time.time() * 1000)
        data['signature'] = self._generate_signature(data)
        data['symbol'] = contract.symbol
        data['orderId'] = order_id

        order_status  = self._make_requests("GET", "/fapi/v1/order", data)

        if order_status:
            order_status = OrderStatus(order_status)

        return order_status

    def _start_ws(self):
        self.ws = websocket.WebSocketApp(self._wss_url,
                                    on_open=self._on_open,
                                    on_close=self._on_close,
                                    on_error= self._on_error,
                                    on_message=self._on_message)
        while True:
            try:
                self.ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
            except Exception as e:
                logger.error("Binance error in run_forever function() method %s", e)
                time.sleep(2)

    def _on_open(self,ws):
        logger.info("Binance Connection Opened")
        self.subscribe_channel(list(self.contracts.values()), "bookTicker")

    def _on_close(self,ws):
        logger.warning("Binance Connection Closed")

    def _on_error(self,ws ,msg: str):
        logger.error("Binance Connection Error %s", msg)

    def _on_message(self, ws ,msg: str):
        # print(msg)
        data = json.loads(msg)
        if "e" in data:
            if data["e"] == "bookTicker":
                symbol = data["s"]
                if symbol not in self.prices:
                    self.prices[symbol] = {'bid': float(data["b"]), 'ask': float(data["a"])}
                else:
                    self.prices[symbol]['bid'] = float(data["b"])
                    self.prices[symbol]['ask'] = float(data["a"])

    def subscribe_channel(self, contracts: typing.List[Contract], channel: str):
        data = dict()
        data["method"] = "SUBSCRIBE"
        data["params"] = []

        for contract in contracts:
            data["params"].append(contract.symbol.lower() + "@" + channel)
        data["id"] = self._ws_id

        try:
            self.ws.send(json.dumps(data))
        except Exception as e:
            logger.error("Websocket error while subscribing to %s %s updated %s", len(contracts), channel ,e)
            return None
        self._ws_id += 1


# def write_log():

# def get_contracts():
#     response_object = requests.get("https://fapi.binance.com/fapi/v1/exchangeInfo")
#     # print(response_object.status_code, response_object.json())
#     # pprint.pprint(response_object.json())
#     # pprint.pprint(response_object.json()['symbols'])
#
#     contracts = []
#
#     for contract in response_object.json()['symbols']:
#         contracts.append(contract["pair"])
#
#     return contracts
#
# print(get_contracts())
#
