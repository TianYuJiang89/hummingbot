import functools
import os
import time
from datetime import datetime
from decimal import Decimal

import numpy as np

# from hummingbot.connector.connector_base import ConnectorBase
from hummingbot.core.data_type.order_book import OrderBook
from hummingbot.core.event.event_forwarder import SourceInfoEventForwarder
from hummingbot.core.event.events import OrderBookEvent, OrderBookTradeEvent
from hummingbot.core.rate_oracle.rate_oracle import RateOracle
from hummingbot.strategy.script_strategy_base import ScriptStrategyBase

import redis
import json

class SimpleDataRecorder(ScriptStrategyBase):
    """
    This example shows how to get the ask and bid of a market and log it to the console.
    """
    ######################################################################################################
    # Begin: Redis Settings
    ######################################################################################################
    # redis_host = "localhost"
    redis_host = os.getenv("CONFIG_HOST_IP")
    redis_port = 6379
    # config_cache_name = "test_instance_markets_cache"
    # data_cache_name = "test_data_cache"
    config_cache_name = "instance_markets_cache"
    data_cache_name = "data_cache"
    log_cache_name = "spend_time"
    heartbeat_cache_name = "lastupddttm"

    pool = redis.ConnectionPool(host=redis_host, port=redis_port, decode_responses=True)
    r = redis.Redis(connection_pool=pool)
    ######################################################################################################
    # End: Redis Settings
    ######################################################################################################

    ######################################################################################################
    # Begin: Record Range Settings
    ######################################################################################################
    # To configure which exchange/ticker need to be record
    INSTANCE_NAME = os.getenv("CONFIG_INSTANCE_ID")
    markets = json.loads(r.hget(config_cache_name, INSTANCE_NAME))
    ######################################################################################################
    # End: Record Range Settings
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
    # trade_list = []
    # initialize dict to store volume weighted average trade price numerator
    vwap_numerator_dict = {(connector_name, asset): 0. for connector_name, assets in markets.items() for asset in
                           assets}

    # quote currency conversion rate
    quote_conversion_rate_dict = {asset.split("-")[1]: None for connector_name, assets in markets.items() for asset in assets}

    ######################################################################################################
    # End: Internal variables
    ######################################################################################################

    ######################################################################################################
    # Begin: Other user define variables
    ######################################################################################################
    # variable for calculating the "dollar amount mid" and "dollar amount bid" and "dollar amount ask"
    volume_measurement_amount = Decimal(100.)
    # portfolio_currency = "USDT"
    portfolio_currency = "USD"

    # notes about quote_conversion_rate:
    # conversion rate = the exchange rate of quote_asset/portfolio_currency
    # For example:
    # USD-CNY = 7.3, BTC-USD = 34000
    # suppose the portfolio currency is CNY, when trading BTC-USD, the quote asset is USD
    # so the conversion rate is the exchange rate of USD/CNY = 7.3
    # the currency of the ticker BTC-USD would be 7.3 * 34000 = 248200

    depth_lvl = int(5)

    ######################################################################################################
    # End: Other user define variables
    ######################################################################################################

    def on_tick(self):
        # if (not self.prepare_ok)&(time.time()-self.prepare_start_time>=60):
        if not self.prepare_ok:
            # check RateOracle
            is_rate_oracle_ok = self.check_rate_oracle()

            # check trade_event subscribed
            if not self.subscribed_to_order_book_trade_event:
                self.subscribe_to_order_book_trade_event()

            # check all
            if is_rate_oracle_ok & self.subscribed_to_order_book_trade_event:
                self.prepare_ok = True

            self.logger().info("!" * 100)
            self.logger().info("is_rate_oracle_ok: %s" % is_rate_oracle_ok)
            self.logger().info("subscribed_to_order_book_trade_event: %s" % self.subscribed_to_order_book_trade_event)
            self.logger().info("prepare_ok: %s" % self.prepare_ok)
            self.logger().info("!" * 100)

        if self.prepare_ok:
            start = time.time()

            self.refresh_conversion_rate_dict()

            quote_list = []
            for connector_name, connector in self.connectors.items():
                for asset in connector.trading_pairs:
                    base_asset, quote_asset = asset.split("-")
                    quote_conversion_rate = self.quote_conversion_rate_dict[quote_asset]
                    mid_price = connector.get_mid_price(asset)
                    amount = self.volume_measurement_amount / (mid_price * quote_conversion_rate)
                    cum_activate_buy_vol, cum_activate_sell_vol = self.active_buy_sell_vol[(connector_name, asset)]
                    qty = cum_activate_buy_vol + cum_activate_sell_vol
                    if qty == 0.:
                        vwap = np.nan
                    else:
                        vwap_numerator = self.vwap_numerator_dict[(connector_name, asset)]
                        vwap = vwap_numerator / qty
                    tick_size = connector.get_order_price_quantum(asset, None)
                    if self.is_perpetual(connector_name):
                        funding_rate = connector.get_funding_info(asset).rate
                    else:
                        funding_rate = 0.

                    # reset the active trade volume counter
                    self.active_buy_sell_vol[(connector_name, asset)] = 0., 0.
                    # reset the volume weighted average trade price numerator
                    self.vwap_numerator_dict[(connector_name, asset)] = 0.

                    p = dict()
                    p["exchange"] = connector_name
                    p["ticker"] = asset
                    # TODO: date-time(exchange provided)
                    p["cabv"] = cum_activate_buy_vol
                    p["casv"] = cum_activate_sell_vol
                    p["vwap"] = vwap
                    p["ts"] = tick_size
                    p["qcr"] = quote_conversion_rate
                    p["funding_rate"] = funding_rate
                    for _ in range(1, self.depth_lvl + 1):
                        bid_result = connector.get_quote_volume_for_base_amount(asset, False, amount * _)
                        avg_bid = bid_result.result_volume / bid_result.query_volume
                        p["bp%s" % _] = avg_bid

                        ask_result = connector.get_quote_volume_for_base_amount(asset, True, amount * _)
                        avg_ask = ask_result.result_volume / ask_result.query_volume
                        p["ap%s" % _] = avg_ask

                    p["time"] = datetime.utcnow().timestamp()

                    quote_list.append(p)

            self.r.hset(self.data_cache_name, self.INSTANCE_NAME, json.dumps(quote_list, default=str))

            end = time.time()
            # self.logger().info("log quote spent time: %s" % (end - start))
            self.r.hset(self.log_cache_name, self.INSTANCE_NAME, (end - start))
            self.r.hset(self.heartbeat_cache_name, self.INSTANCE_NAME, datetime.utcnow().timestamp())

            # start = time.time()
            # self.logger().info("len(trade_list): %s" % len(self.trade_list))
            # with self.client.write_api(write_options=SYNCHRONOUS) as write_api:
            #     write_api.write(bucket=self.bucket, record=self.trade_list, org=self.org)
            # self.trade_list = []
            # end = time.time()
            # self.logger().info("log trade spent time: %s" % (end - start))

    def refresh_conversion_rate_dict(self):
        for quote_asset in self.quote_conversion_rate_dict:
            asset = quote_asset + "-" + self.portfolio_currency
            conversion_rate = RateOracle.get_instance().get_pair_rate(asset)
            if conversion_rate is not None:
                self.quote_conversion_rate_dict[quote_asset] = conversion_rate

    def check_rate_oracle(self):
        self.refresh_conversion_rate_dict()
        for quote_asset, conversion_rate in self.quote_conversion_rate_dict.items():
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
        '''
        for connector_name, connector in self.connectors.items():
            for order_book_name, order_book in connector.order_books.items():
                setattr(self, f"_partial_process_public_trade_{connector_name}_{order_book_name}",
                        functools.partial(self._process_public_trade, connector_name=connector_name))
                setattr(self, f"_trade_event_forwarder_{connector_name}_{order_book_name}", SourceInfoEventForwarder(
                    getattr(self, f"_partial_process_public_trade_{connector_name}_{order_book_name}")))
                order_book.add_listener(OrderBookEvent.TradeEvent,
                                        getattr(self, f"_trade_event_forwarder_{connector_name}_{order_book_name}"))
        '''
        for connector_name, connector in self.connectors.items():
            setattr(self, f"_partial_process_public_trade_{connector_name}",
                    functools.partial(self._process_public_trade, connector_name=connector_name))
            setattr(self, f"_trade_event_forwarder_{connector_name}", SourceInfoEventForwarder(
                getattr(self, f"_partial_process_public_trade_{connector_name}")))
            for order_book_name, order_book in connector.order_books.items():
                order_book.add_listener(OrderBookEvent.TradeEvent,
                                        getattr(self, f"_trade_event_forwarder_{connector_name}"))
        self.subscribed_to_order_book_trade_event = True

    def _process_public_trade(self, event_tag: int, order_book: OrderBook, event: OrderBookTradeEvent,
                              connector_name: str):
        """
        Add new trade to list, remove old trade event, if count greater than trade_count_limit.
        """
        asset = event.trading_pair
        # type_name = event.type.name
        price = event.price
        amount = event.amount
        # is_taker = event.is_taker

        # calculate cumulative active buy and sell volumes
        cum_activate_buy_vol, cum_activate_sell_vol = self.active_buy_sell_vol[(connector_name, asset)]
        if event.type.name == "BUY":
            cum_activate_buy_vol = cum_activate_buy_vol + amount
        elif event.type.name == "SELL":
            cum_activate_sell_vol = cum_activate_sell_vol + amount
        self.active_buy_sell_vol[(connector_name, asset)] = cum_activate_buy_vol, cum_activate_sell_vol

        # calculate volume weighted average trade price
        # vwap = sum(trade_price * trade_volumn)/sum(trade_volumn)
        # because we only know the total volumn when the snapshot period finished
        # so, let caculate the Numerator first
        self.vwap_numerator_dict[(connector_name, asset)] = self.vwap_numerator_dict[(connector_name, asset)] + price * amount

        # record trades
        # p = Point("trades")
        # p.tag("exchange", connector_name)
        # p.tag("ticker", asset)
        # p.field("timestamp", timestamp)
        # p.field("type", type_name)
        # p.field("price", price)
        # p.field("amount", amount)
        # p.field("is_taker", is_taker)
        # p.time(datetime.utcnow(), WritePrecision.NS)
        #
        # self.trade_list.append(p)
