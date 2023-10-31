import os
import time
from datetime import datetime
from decimal import Decimal

from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

from hummingbot.connector.connector_base import ConnectorBase
from hummingbot.core.data_type.order_book import OrderBook
from hummingbot.core.event.event_forwarder import SourceInfoEventForwarder
from hummingbot.core.event.events import OrderBookEvent, OrderBookTradeEvent
from hummingbot.core.rate_oracle.rate_oracle import RateOracle
from hummingbot.strategy.script_strategy_base import ScriptStrategyBase

import functools

class SimpleDataRecorder(ScriptStrategyBase):
    """
    This example shows how to get the ask and bid of a market and log it to the console.
    """
    ######################################################################################################
    # Begin: Record Range Settings
    ######################################################################################################
    # To configure which exchange/ticker need to be record
    markets = {
        'binance_perpetual': {
            'TLM-USDT', 'CYBER-USDT', 'HIGH-USDT', 'ZIL-USDT', 'SAND-USDT', 'RLC-USDT', 'ENJ-USDT', 'STX-USDT', 'ATOM-USDT', 'OXT-USDT',
            'TOMO-USDT', 'ONT-USDT', 'OP-USDT', 'IOTX-USDT', 'QNT-USDT', 'RAD-USDT', 'ETC-USDT', 'ANKR-USDT', 'EGLD-USDT', 'OCEAN-USDT',
            'LDO-USDT', 'ENS-USDT', 'MASK-USDT', 'XTZ-USDT', 'IOST-USDT', 'UNFI-USDT', 'RVN-USDT', 'RDNT-USDT', 'ZEC-USDT', 'COTI-USDT',
            'TRX-USDT', 'FTM-USDT', 'LINA-USDT', 'RNDR-USDT', 'HBAR-USDT', 'ICX-USDT', 'XEM-USDT', 'KAVA-USDT', 'CVX-USDT', 'UMA-USDT',
            'MDT-USDT', 'DODOX-USDT', 'BAL-USDT', 'AGIX-USDT', 'BLUEBIRD-USDT', 'SUSHI-USDT', 'RSR-USDT', 'GALA-USDT', 'CHZ-USDT', 'KEY-USDT',
            'FLM-USDT', 'AGLD-USDT', 'PERP-USDT', 'REEF-USDT', 'BAT-USDT', 'STMX-USDT', 'STG-USDT', 'FOOTBALL-USDT', 'BAND-USDT', 'XMR-USDT',
            'FLOW-USDT', 'DGB-USDT', '1000SHIB-USDT', 'ICP-USDT', 'ALICE-USDT', 'IOTA-USDT', 'YFI-USDT', '1000LUNC-USDT', 'ANT-USDT', 'T-USDT',
            'AUDIO-USDT', 'UNI-USDT', 'XRP-USDT', 'ZRX-USDT', 'MATIC-USDT', 'ONE-USDT', 'DEFI-USDT', 'MINA-USDT', 'CFX-USDT', 'CELR-USDT',
            'COMP-USDT', 'FET-USDT', 'JASMY-USDT', 'GAL-USDT', 'BLZ-USDT', 'XVG-USDT', 'NEAR-USDT', 'STORJ-USDT', 'SOL-USDT', 'AMB-USDT',
            'CTSI-USDT', 'SKL-USDT', 'WLD-USDT', 'BLUR-USDT', 'CHR-USDT', 'WOO-USDT', 'AAVE-USDT', 'AR-USDT', 'MKR-USDT', 'IMX-USDT',
            'YGG-USDT', 'APE-USDT', 'GMT-USDT', 'LPT-USDT', 'NKN-USDT', 'IDEX-USDT', 'HOT-USDT', 'THETA-USDT', 'DUSK-USDT', 'GRT-USDT',
            'XVS-USDT', 'FXS-USDT', 'WAVES-USDT', 'LIT-USDT', 'BEL-USDT', 'PENDLE-USDT', 'BNX-USDT', 'QTUM-USDT', 'CTK-USDT', 'HFT-USDT',
            'INJ-USDT', 'CELO-USDT', 'SNX-USDT', 'LUNA2-USDT', '1000PEPE-USDT', 'APT-USDT', 'ARPA-USDT', 'OMG-USDT', 'NMR-USDT', 'MAV-USDT',
            'BNB-USDT', 'XLM-USDT', 'DYDX-USDT', 'MTL-USDT', 'ATA-USDT', 'SEI-USDT', 'JOE-USDT', 'PEOPLE-USDT', 'KSM-USDT', 'LEVER-USDT',
            'MANA-USDT', 'ROSE-USDT', 'AXS-USDT', 'ADA-USDT', 'ACH-USDT', 'BAKE-USDT', 'HOOK-USDT', 'ETH-USDT', 'SFP-USDT', 'MAGIC-USDT',
            'NEO-USDT', 'VET-USDT', 'OGN-USDT', 'EOS-USDT', 'BNT-USDT', 'CRV-USDT', 'ALPHA-USDT', 'RUNE-USDT', 'ARB-USDT', 'DENT-USDT',
            '1000XEC-USDT', 'DAR-USDT', 'AVAX-USDT', 'BCH-USDT', 'DOT-USDT', 'DASH-USDT', 'ID-USDT', 'ARKM-USDT', 'PHB-USDT', 'CKB-USDT',
            'KLAY-USDT', 'EDU-USDT', 'LINK-USDT', 'REN-USDT', 'KNC-USDT', 'C98-USDT', 'FIL-USDT', 'LRC-USDT', '1INCH-USDT', 'SSV-USDT',
            'ZEN-USDT', 'TRU-USDT', 'ASTR-USDT', 'TRB-USDT', 'ALGO-USDT', 'API3-USDT', 'LQTY-USDT', 'SPELL-USDT', 'COMBO-USDT', 'GTC-USDT',
            'GMX-USDT', 'SXP-USDT', 'LTC-USDT', 'DOGE-USDT', 'SUI-USDT'
        }
    }

    ######################################################################################################
    # End: Record Range Settings
    ######################################################################################################

    ######################################################################################################
    # Begin: InfluxDB setting
    ######################################################################################################
    url = "http://localhost:8086"
    org = "hummingbot"
    bucket = "new"
    token = os.getenv("INFLUXDB_TOKEN")

    client = InfluxDBClient(url=url, token=token)
    ######################################################################################################
    # End: InfluxDB setting
    ######################################################################################################

    ######################################################################################################
    # Begin: Internal variables
    ######################################################################################################
    # should not modify
    subscribed_to_order_book_trade_event = False
    prepare_ok = False

    # initialize dict to store active buy sell volumes
    active_buy_sell_vol = {(connector_name, asset): (0., 0.) for connector_name, assets in markets.items() for asset in
                           assets}
    # to record actual trades happened within the interval
    trade_list = []

    ######################################################################################################
    # End: Internal variables
    ######################################################################################################

    ######################################################################################################
    # Begin: Other user define variables
    ######################################################################################################
    # variable for calculating the "dollar amount mid" and "dollar amount bid" and "dollar amount ask"
    vol_measurement_usd_amount = Decimal(100.)

    depth_lvl = int(5)

    ######################################################################################################
    # End: Other user define variables
    ######################################################################################################

    def on_tick(self):
        #if (not self.prepare_ok)&(time.time()-self.prepare_start_time>=60):
        if not self.prepare_ok:
            # check RateOracle
            # is_rate_oracle_ok = self.check_rate_oracle()
            is_rate_oracle_ok = True

            # check trade_event subscribed
            if not self.subscribed_to_order_book_trade_event:
                self.subscribe_to_order_book_trade_event()
                # self.subscribed_to_order_book_trade_event = True

            # check influxdb
            is_influxdb_ok = self.client.ping()

            # check all
            if is_rate_oracle_ok & self.subscribed_to_order_book_trade_event & is_influxdb_ok:
                self.prepare_ok = True

            self.logger().info("!"*100)
            self.logger().info("is_rate_oracle_ok: %s" % is_rate_oracle_ok)
            self.logger().info("subscribed_to_order_book_trade_event: %s" % self.subscribed_to_order_book_trade_event)
            self.logger().info("is_influxdb_ok: %s" % is_influxdb_ok)
            self.logger().info("prepare_ok: %s" % self.prepare_ok)
            self.logger().info("!" * 100)
            
        if self.prepare_ok:
            start = time.time()

            quote_list = []
            for connector_name, connector in self.connectors.items():
                for asset in self.markets[connector_name]:
                    # conversion_rate = RateOracle.get_instance().get_pair_rate(asset)
                    conversion_rate = connector.get_mid_price(asset)
                    amount = self.vol_measurement_usd_amount / conversion_rate
                    cum_activate_buy_vol, cum_activate_sell_vol = self.active_buy_sell_vol[(connector_name, asset)]
                    if self.is_perpetual(connector_name):
                        funding_rate = connector.get_funding_info(asset).rate
                    else:
                        funding_rate = 0.

                    # reset the active trade volume counter
                    self.active_buy_sell_vol[(connector_name, asset)] = 0., 0.

                    p = Point("quotes")
                    p.tag("exchange", connector_name)
                    p.tag("ticker", asset)
                    # TODO: date-time(exchange provided)
                    p.field("cabv", cum_activate_buy_vol)
                    p.field("casv", cum_activate_sell_vol)
                    p.field("funding_rate", funding_rate)
                    for _ in range(1, self.depth_lvl + 1):
                        bid_result = connector.get_quote_volume_for_base_amount(asset, False, amount * _)
                        avg_bid = bid_result.result_volume / bid_result.query_volume
                        p.field("bp%s" % _, avg_bid)

                        ask_result = connector.get_quote_volume_for_base_amount(asset, True, amount * _)
                        avg_ask = ask_result.result_volume / ask_result.query_volume
                        p.field("ap%s" % _, avg_ask)

                    p.time(datetime.utcnow(), WritePrecision.NS)

                    quote_list.append(p)

            with self.client.write_api(write_options=SYNCHRONOUS) as write_api:
                write_api.write(bucket=self.bucket, record=quote_list, org=self.org)

            end = time.time()
            self.logger().info("log quote spent time: %s" % (end - start))

            start = time.time()
            # self.logger().info("len(trade_list): %s" % len(self.trade_list))
            with self.client.write_api(write_options=SYNCHRONOUS) as write_api:
                write_api.write(bucket=self.bucket, record=self.trade_list, org=self.org)
            self.trade_list = []
            end = time.time()
            self.logger().info("log trade spent time: %s" % (end - start))

    def check_rate_oracle(self):
        for connector_name, connector in self.connectors.items():
            for asset in self.markets[connector_name]:
                conversion_rate = RateOracle.get_instance().get_pair_rate(asset)
                if conversion_rate is None:
                    return False
        return True

    def is_perpetual(self, exchange):
        """
        Checks if the exchange is a perpetual market.
        """
        return "perpetual" in exchange

    def subscribe_to_order_book_trade_event(self):
        """
        Subscribe to raw trade event.
        """
        for connector_name, connector in self.connectors.items():
            for order_book_name, order_book in connector.order_books.items():
                setattr(self, f"_partial_process_public_trade_{connector_name}_{order_book_name}",
                        functools.partial(self._process_public_trade, connector_name=connector_name))
                setattr(self, f"_trade_event_forwarder_{connector_name}_{order_book_name}", SourceInfoEventForwarder(
                    getattr(self, f"_partial_process_public_trade_{connector_name}_{order_book_name}")))
                order_book.add_listener(OrderBookEvent.TradeEvent,
                                        getattr(self, f"_trade_event_forwarder_{connector_name}_{order_book_name}"))
        self.subscribed_to_order_book_trade_event = True

    def _process_public_trade(self, event_tag: int, order_book: OrderBook, event: OrderBookTradeEvent,
                              connector_name: str):
        """
        Add new trade to list, remove old trade event, if count greater than trade_count_limit.
        """
        asset = event.trading_pair
        timestamp = event.trading_pair
        type_name = event.type.name
        price = event.price
        amount = event.amount
        is_taker = event.is_taker

        # calculate cumulative active buy and sell volumes
        cum_activate_buy_vol, cum_activate_sell_vol = self.active_buy_sell_vol[(connector_name, asset)]
        if event.type.name == "BUY":
            cum_activate_buy_vol = cum_activate_buy_vol + amount
        elif event.type.name == "SELL":
            cum_activate_sell_vol = cum_activate_sell_vol + amount
        self.active_buy_sell_vol[(connector_name, asset)] = cum_activate_buy_vol, cum_activate_sell_vol

        # record trades
        p = Point("trades")
        p.tag("exchange", connector_name)
        p.tag("ticker", asset)
        p.field("timestamp", timestamp)
        p.field("type", type_name)
        p.field("price", price)
        p.field("amount", amount)
        p.field("is_taker", is_taker)
        p.time(datetime.utcnow(), WritePrecision.NS)

        self.trade_list.append(p)


