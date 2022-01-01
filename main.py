import tkinter as tk
import logging
from connectors.binance_futures import BinanceFutureClient
# from binance_futures import write_log
from interface.root_component import Root

logger = logging.getLogger()

logger.setLevel(logging.INFO)


stream_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(levelname)s :: %(message)s')
stream_handler.setFormatter(formatter)
stream_handler.setLevel(logging.INFO)

file_handler = logging.FileHandler('info.log')
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.DEBUG)

logger.addHandler(stream_handler)
logger.addHandler(file_handler)


if __name__ == "__main__":

    binance = BinanceFutureClient("<Your_PUBLIC_KEY>","<YOUR_SECRET_KEY>",True)
    # print(binance.get_historical_candles("BTCUSDT","1h"))
    # candles  = binance.get_historical_candles("BTCUSDT", "1h")
    #print(candless[-1].high)
    # print(binance.get_balances())
    # print(binance.get_contracts())
    root = Root(binance)
    root.mainloop()

    # root.configure(bg='gray12')
    # i = 0
    # j = 0
    #
    # calibari_font = ("Calibari", 11, "normal ")
    #
    # for  contract in bitmax_conracts:
    #     label_widget = tk.Label(root,text=contract, bg='gray12', fg= 'SteelBlue' , width=13)
    #     label_widget.grid(row=i,column=j, sticky='ew')
    #
    #     if i == 4:
    #         j += 1
    #         i = 0
    #     else:
    #          i += 1

