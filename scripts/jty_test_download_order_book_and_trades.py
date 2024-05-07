import json
import os
from datetime import datetime
from typing import Dict

from hummingbot import data_path
from hummingbot.connector.connector_base import ConnectorBase
from hummingbot.core.event.event_forwarder import SourceInfoEventForwarder
from hummingbot.core.event.events import OrderBookEvent, OrderBookTradeEvent
from hummingbot.strategy.script_strategy_base import ScriptStrategyBase


class DownloadTradesAndOrderBookSnapshots(ScriptStrategyBase):
    # exchange = os.getenv("EXCHANGE", "binance_paper_trade")
    # trading_pairs = os.getenv("TRADING_PAIRS", "ETH-USDT,BTC-USDT")
    exchange = "binance_perpetual"
    trading_pairs = 'BTC-USDT,ETH-USDT,BCH-USDT,XRP-USDT,EOS-USDT,LTC-USDT,TRX-USDT,ETC-USDT,LINK-USDT,XLM-USDT,ADA-USDT,XMR-USDT,DASH-USDT,ZEC-USDT,XTZ-USDT,BNB-USDT,ATOM-USDT,ONT-USDT,IOTA-USDT,BAT-USDT,VET-USDT,NEO-USDT,QTUM-USDT,IOST-USDT,THETA-USDT,ALGO-USDT,ZIL-USDT,KNC-USDT,ZRX-USDT,COMP-USDT,OMG-USDT,DOGE-USDT,SXP-USDT,KAVA-USDT,BAND-USDT,RLC-USDT,WAVES-USDT,MKR-USDT,SNX-USDT,DOT-USDT,DEFI-USDT,YFI-USDT,BAL-USDT,CRV-USDT,TRB-USDT,RUNE-USDT,SUSHI-USDT,EGLD-USDT,SOL-USDT,ICX-USDT,STORJ-USDT,BLZ-USDT,UNI-USDT,AVAX-USDT,FTM-USDT,ENJ-USDT,FLM-USDT,TOMO-USDT,REN-USDT,KSM-USDT,NEAR-USDT,AAVE-USDT,FIL-USDT,RSR-USDT,LRC-USDT,MATIC-USDT,OCEAN-USDT,BEL-USDT,CTK-USDT,AXS-USDT,ALPHA-USDT,ZEN-USDT,SKL-USDT,GRT-USDT,1INCH-USDT,BTC-BUSD,CHZ-USDT,SAND-USDT,ANKR-USDT,LIT-USDT,UNFI-USDT,REEF-USDT,RVN-USDT,SFP-USDT,XEM-USDT,COTI-USDT,CHR-USDT,MANA-USDT,ALICE-USDT,HBAR-USDT,ONE-USDT,LINA-USDT,STMX-USDT,DENT-USDT,CELR-USDT,HOT-USDT,MTL-USDT,OGN-USDT,NKN-USDT,DGB-USDT,1000SHIB-USDT,BAKE-USDT,GTC-USDT,ETH-BUSD,BTCDOM-USDT,BNB-BUSD,XRP-BUSD,IOTX-USDT,AUDIO-USDT,C98-USDT,MASK-USDT,ATA-USDT,DYDX-USDT,1000XEC-USDT,GALA-USDT,CELO-USDT,AR-USDT,KLAY-USDT,ARPA-USDT,CTSI-USDT,LPT-USDT,ENS-USDT,PEOPLE-USDT,ANT-USDT,ROSE-USDT,DUSK-USDT,FLOW-USDT,IMX-USDT,API3-USDT,GMT-USDT,APE-USDT,WOO-USDT,JASMY-USDT,DAR-USDT,GAL-USDT,OP-USDT,INJ-USDT,STG-USDT,FOOTBALL-USDT,SPELL-USDT,1000LUNC-USDT,LUNA2-USDT,LDO-USDT,CVX-USDT,ICP-USDT,APT-USDT,QNT-USDT,BLUEBIRD-USDT,FET-USDT,FXS-USDT,HOOK-USDT,MAGIC-USDT,T-USDT,RNDR-USDT,HIGH-USDT,MINA-USDT,ASTR-USDT,AGIX-USDT,PHB-USDT,GMX-USDT,CFX-USDT,STX-USDT,BNX-USDT,ACH-USDT,SSV-USDT,CKB-USDT,PERP-USDT,TRU-USDT,LQTY-USDT,USDC-USDT,ID-USDT,ARB-USDT,JOE-USDT,TLM-USDT,AMB-USDT,LEVER-USDT,RDNT-USDT,HFT-USDT,XVS-USDT,ETH-BTC,BLUR-USDT,EDU-USDT,IDEX-USDT,SUI-USDT,1000PEPE-USDT,1000FLOKI-USDT,UMA-USDT,RAD-USDT,KEY-USDT,COMBO-USDT,NMR-USDT,MAV-USDT,MDT-USDT,XVG-USDT,WLD-USDT,PENDLE-USDT,ARKM-USDT,AGLD-USDT,YGG-USDT,DODOX-USDT,BNT-USDT,OXT-USDT,SEI-USDT,BTC-USDT,ETH-USDT,CYBER-USDT,HIFI-USDT,ARK-USDT,FRONT-USDT,GLMR-USDT,BICO-USDT,BTC-USDT,ETH-USDT,STRAX-USDT,LOOM-USDT,BIGTIME-USDT,BOND-USDT,ORBS-USDT,STPT-USDT,WAXP-USDT,BSV-USDT,RIF-USDT,POLYX-USDT,GAS-USDT,POWR-USDT,SLP-USDT'
    depth = int(os.getenv("DEPTH", 50))
    trading_pairs = [pair for pair in trading_pairs.split(",")]
    last_dump_timestamp = 0
    time_between_csv_dumps = 10

    ob_temp_storage = {trading_pair: [] for trading_pair in trading_pairs}
    trades_temp_storage = {trading_pair: [] for trading_pair in trading_pairs}
    current_date = None
    ob_file_paths = {}
    trades_file_paths = {}
    markets = {exchange: set(trading_pairs)}
    subscribed_to_order_book_trade_event: bool = False

    def __init__(self, connectors: Dict[str, ConnectorBase]):
        super().__init__(connectors)
        self.create_order_book_and_trade_files()
        self.order_book_trade_event = SourceInfoEventForwarder(self._process_public_trade)

    def on_tick(self):
        if not self.subscribed_to_order_book_trade_event:
            self.subscribe_to_order_book_trade_event()
        self.check_and_replace_files()
        for trading_pair in self.trading_pairs:
            order_book_data = self.get_order_book_dict(self.exchange, trading_pair, self.depth)
            self.ob_temp_storage[trading_pair].append(order_book_data)
        if self.last_dump_timestamp < self.current_timestamp:
            self.dump_and_clean_temp_storage()

    def get_order_book_dict(self, exchange: str, trading_pair: str, depth: int = 50):
        order_book = self.connectors[exchange].get_order_book(trading_pair)
        snapshot = order_book.snapshot
        return {
            "ts": self.current_timestamp,
            "bids": snapshot[0].loc[:(depth - 1), ["price", "amount"]].values.tolist(),
            "asks": snapshot[1].loc[:(depth - 1), ["price", "amount"]].values.tolist(),
        }

    def dump_and_clean_temp_storage(self):
        for trading_pair, order_book_info in self.ob_temp_storage.items():
            file = self.ob_file_paths[trading_pair]
            json_strings = [json.dumps(obj) for obj in order_book_info]
            json_data = '\n'.join(json_strings)
            file.write(json_data)
            self.ob_temp_storage[trading_pair] = []
        for trading_pair, trades_info in self.trades_temp_storage.items():
            file = self.trades_file_paths[trading_pair]
            json_strings = [json.dumps(obj) for obj in trades_info]
            json_data = '\n'.join(json_strings)
            file.write(json_data)
            self.trades_temp_storage[trading_pair] = []
        self.last_dump_timestamp = self.current_timestamp + self.time_between_csv_dumps

    def check_and_replace_files(self):
        current_date = datetime.now().strftime("%Y-%m-%d")
        if current_date != self.current_date:
            for file in self.ob_file_paths.values():
                file.close()
            self.create_order_book_and_trade_files()

    def create_order_book_and_trade_files(self):
        self.current_date = datetime.now().strftime("%Y-%m-%d")
        self.ob_file_paths = {trading_pair: self.get_file(self.exchange, trading_pair, "order_book_snapshots", self.current_date) for
                              trading_pair in self.trading_pairs}
        self.trades_file_paths = {trading_pair: self.get_file(self.exchange, trading_pair, "trades", self.current_date) for
                                  trading_pair in self.trading_pairs}

    @staticmethod
    def get_file(exchange: str, trading_pair: str, source_type: str, current_date: str):
        file_path = data_path() + f"/{exchange}_{trading_pair}_{source_type}_{current_date}.txt"
        return open(file_path, "a")

    def _process_public_trade(self, event_tag: int, market: ConnectorBase, event: OrderBookTradeEvent):
        self.trades_temp_storage[event.trading_pair].append({
            "ts": event.timestamp,
            "price": event.price,
            "q_base": event.amount,
            "side": event.type.name.lower(),
        })

    def subscribe_to_order_book_trade_event(self):
        for market in self.connectors.values():
            for order_book in market.order_books.values():
                order_book.add_listener(OrderBookEvent.TradeEvent, self.order_book_trade_event)
        self.subscribed_to_order_book_trade_event = True
