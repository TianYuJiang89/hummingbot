import functools
import os
import time
from datetime import datetime, timezone
from decimal import Decimal

import numpy as np

# from hummingbot.connector.connector_base import ConnectorBase
from hummingbot.core.data_type.order_book import OrderBook
from hummingbot.core.event.event_forwarder import SourceInfoEventForwarder
from hummingbot.core.event.events import OrderBookEvent, OrderBookTradeEvent
from hummingbot.core.rate_oracle.rate_oracle import RateOracle
from hummingbot.strategy.script_strategy_base import ScriptStrategyBase

import redis
import orjson as json

class SimpleDataRecorder(ScriptStrategyBase):
    """
    This example shows how to get the ask and bid of a market and log it to the console.
    """
    ######################################################################################################
    # Begin: Redis Settings
    ######################################################################################################
    # redis_host = "localhost"
    redis_host = os.getenv("REDIS_HOST_IP")
    redis_port = 6379
    # config_cache_name = "test_instance_markets_cache"
    # data_cache_name = "test_data_cache"
    config_cache_name = "md_instance_markets_cache"
    data_cache_name = "data_cache"
    log_cache_name = "spend_time"
    heartbeat_cache_name = "lastupddttm"
    trade_listener_heartbeat_cache_name = "trade_listener_lastupddttm"

    pool = redis.ConnectionPool(host=redis_host, port=redis_port, decode_responses=True)
    r = redis.Redis(connection_pool=pool)
    ######################################################################################################
    # End: Redis Settings
    ######################################################################################################

    ######################################################################################################
    # Begin: Record Range Settings
    ######################################################################################################
    # To configure which exchange/ticker need to be record
    VPS_INSTANCE_ID = os.getenv("VPS_INSTANCE_ID")
    INSTANCE_NAME = os.getenv("CONFIG_INSTANCE_ID")
    markets = json.loads(r.hget(config_cache_name, VPS_INSTANCE_ID))[INSTANCE_NAME]
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

    # to trace the trade processor heartbeat
    has_trade_listener_run_dict = {(connector_name, asset): False for connector_name, assets in markets.items() for asset in assets}
    # to check if the orderbook re-init, if it is, then re-sub the trade processor function
    order_book_id_dict = {(connector_name, asset): None for connector_name, assets in markets.items() for asset in assets}
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
            # start = time.time()

            self.refresh_conversion_rate_dict()

            # quote_list = []
            quote_dict = dict()
            lastupddttm_dict = dict()
            trade_lastupddttm_dict = dict()
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
                    order_size = connector.get_order_size_quantum(asset, None)
                    min_notional_size = connector.trading_rules[asset].min_notional_size
                    if self.is_perpetual(connector_name):
                        funding_rate = connector.get_funding_info(asset).rate
                    else:
                        funding_rate = 0.

                    # reset the active trade volume counter
                    self.active_buy_sell_vol[(connector_name, asset)] = 0., 0.
                    # reset the volume weighted average trade price numerator
                    self.vwap_numerator_dict[(connector_name, asset)] = 0.

                    p = dict()
                    p["influx_point"] = "quotes"
                    p["influx_bucket"] = connector_name + "_md"
                    p["influx_tag_keys"] = ["exchange", "ticker"]

                    p["exchange"] = connector_name
                    p["ticker"] = asset
                    # TODO: date-time(exchange provided)
                    p["cabv"] = cum_activate_buy_vol
                    p["casv"] = cum_activate_sell_vol
                    p["vwap"] = vwap
                    p["ts"] = float(tick_size)
                    p["os"] = float(order_size)
                    p["mns"] = float(min_notional_size)
                    p["qcr"] = float(quote_conversion_rate)
                    p["funding_rate"] = float(funding_rate)
                    for _ in range(1, self.depth_lvl + 1):
                        bid_result = connector.get_quote_volume_for_base_amount(asset, False, amount * _)
                        avg_bid = bid_result.result_volume / bid_result.query_volume
                        p["bp%s" % _] = float(avg_bid)

                        ask_result = connector.get_quote_volume_for_base_amount(asset, True, amount * _)
                        avg_ask = ask_result.result_volume / ask_result.query_volume
                        p["ap%s" % _] = float(avg_ask)

                    utcnow_stamp = datetime.now(tz=timezone.utc).timestamp()
                    p["time"] = float(utcnow_stamp)

                    # quote_list.append(p)
                    key = json.dumps((connector_name, asset))
                    quote_dict[key] = json.dumps(p)
                    lastupddttm_dict[key] = utcnow_stamp
                    if self.has_trade_listener_run_dict[(connector_name, asset)]:
                        trade_lastupddttm_dict[key] = utcnow_stamp
                        self.has_trade_listener_run_dict[(connector_name, asset)] = False

            # self.r.hset(self.data_cache_name, self.INSTANCE_NAME, json.dumps(quote_list, default=str))
            self.r.hset(self.data_cache_name, mapping=quote_dict)
            self.r.hset(self.heartbeat_cache_name, mapping=lastupddttm_dict)
            if len(trade_lastupddttm_dict) > 0:
                self.r.hset(self.trade_listener_heartbeat_cache_name, mapping=trade_lastupddttm_dict)

            self.subscribe_to_order_book_trade_event()

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
        for connector_name, connector in self.connectors.items():
            partial_func_name = f"_partial_process_public_trade_{connector_name}"
            forwarder_func_name = f"_trade_event_forwarder_{connector_name}"
            if not hasattr(self, partial_func_name):
                setattr(self, partial_func_name,
                    functools.partial(self._process_public_trade, connector_name=connector_name))
            if not hasattr(self, forwarder_func_name):
                setattr(self, forwarder_func_name, SourceInfoEventForwarder(
                    getattr(self, partial_func_name)))
            for order_book_name, order_book in connector.order_books.items():
                old_order_book_id = self.order_book_id_dict[(connector_name, order_book_name)]
                new_order_book_id = id(order_book)
                if old_order_book_id is None or new_order_book_id != old_order_book_id:
                    order_book.add_listener(OrderBookEvent.TradeEvent,
                                        getattr(self, forwarder_func_name))
                    self.order_book_id_dict[(connector_name, order_book_name)] = new_order_book_id
                    self.logger().info(f"Subscribe to raw trade event for {order_book_name}. completed.")

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

        self.has_trade_listener_run_dict[(connector_name, asset)] = True