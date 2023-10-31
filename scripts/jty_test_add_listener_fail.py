import functools

# from hummingbot.connector.connector_base import ConnectorBase
from hummingbot.core.data_type.order_book import OrderBook
from hummingbot.core.event.event_forwarder import SourceInfoEventForwarder
from hummingbot.core.event.events import OrderBookEvent, OrderBookTradeEvent

# , OrderFilledEvent)
# from hummingbot.core.rate_oracle.rate_oracle import RateOracle
from hummingbot.strategy.script_strategy_base import ScriptStrategyBase


class TestExample(ScriptStrategyBase):
    """
    This example shows how to get the ask and bid of a market and log it to the console.
    """
    markets = {
        'binance_perpetual': {
            'BTC-USDT', 'ETH-USDT',
        }
    }

    subscribed_to_order_book_trade_event = False
    prepare_ok = False

    active_buy_sell_vol = {(connector_name, asset): (0., 0.) for connector_name, assets in markets.items() for asset in assets}

    trade_list = []

    test_counter = 0

    def on_tick(self):
        if not self.prepare_ok:
            # check trade_event subscribed
            if not self.subscribed_to_order_book_trade_event:
                self.subscribe_to_order_book_trade_event()
                # self.subscribed_to_order_book_trade_event = True

            # check all
            if self.subscribed_to_order_book_trade_event:
                self.prepare_ok = True

            #

            self.logger().info("prepare_ok: %s" % self.prepare_ok)

        else:

            for connector_name, connector in self.connectors.items():
                for asset in self.markets[connector_name]:
                    # conversion_rate = RateOracle.get_instance().get_pair_rate(asset)

                    self.logger().info(f"Connector: {connector_name} Asset: {asset} Mid price: {connector.get_mid_price(asset)}")

                    # reset the active trade volume counter
                    self.active_buy_sell_vol[(connector_name, asset)] = 0., 0.

                    for event in self.trade_list:
                        self.logger().info(f"event: {event}")
                    self.trade_list = []

                    # self.logger().info(f"#"*100)

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
                setattr(self, f"_partial_process_public_trade_{connector_name}_{order_book_name}", functools.partial(self._process_public_trade, connector_name=connector_name))
                setattr(self, f"_trade_event_forwarder_{connector_name}_{order_book_name}", SourceInfoEventForwarder(getattr(self, f"_partial_process_public_trade_{connector_name}_{order_book_name}")))
                order_book.add_listener(OrderBookEvent.TradeEvent, getattr(self, f"_trade_event_forwarder_{connector_name}_{order_book_name}"))
        self.subscribed_to_order_book_trade_event = True

    def _process_public_trade(self, event_tag: int, order_book: OrderBook, event: OrderBookTradeEvent, connector_name: str):
        """
        Add new trade to list, remove old trade event, if count greater than trade_count_limit.
        """
        # self.logger().info(f"OrderBookTradeEvent connector_name {connector_name}")
        # self.logger().info(f"OrderBookTradeEvent trading_pair {event.trading_pair}")
        # self.logger().info(f"OrderBookTradeEvent timestamp {event.timestamp}")
        # self.logger().info(f"OrderBookTradeEvent type {event.type.name}")
        # self.logger().info(f"OrderBookTradeEvent price {event.price}")
        # self.logger().info(f"OrderBookTradeEvent amount {event.amount}")
        # self.logger().info(f"OrderBookTradeEvent is_taker {event.is_taker}")

        # calculate cumulative active buy and sell volumes
        asset = event.trading_pair
        cum_activate_buy_vol, cum_activate_sell_vol = self.active_buy_sell_vol[(connector_name, asset)]
        if event.type.name == " BUY":
            cum_activate_buy_vol = cum_activate_buy_vol + event.amount
        elif event.type.name == "SELL":
            cum_activate_sell_vol = cum_activate_sell_vol + event.amount
        self.active_buy_sell_vol[(connector_name, asset)] = cum_activate_buy_vol, cum_activate_sell_vol

        self.trade_list.append(event)

        self.test_counter = self.test_counter + 1
        self.logger().info(f"test_counter={self.test_counter}")
        if self.test_counter > 20:
            raise Exception("Fuck!!!!!!")
