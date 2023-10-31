from hummingbot.core.rate_oracle.rate_oracle import RateOracle
from hummingbot.strategy.script_strategy_base import ScriptStrategyBase
#from hummingbot.connector.connector_base import ConnectorBase
from hummingbot.core.data_type.order_book import OrderBook
from hummingbot.core.event.event_forwarder import SourceInfoEventForwarder
from hummingbot.core.event.events import OrderBookEvent, OrderBookTradeEvent, OrderFilledEvent

import functools

class TestExample(ScriptStrategyBase):
    """
    This example shows how to get the ask and bid of a market and log it to the console.
    """
    markets = {
        'binance_perpetual': {
            #'TLM-USDT', 'CYBER-USDT', 'HIGH-USDT', 'ZIL-USDT', 'SAND-USDT', 'RLC-USDT', 'ENJ-USDT', 'STX-USDT', 'ATOM-USDT', 'OXT-USDT',
            # 'TOMO-USDT', 'ONT-USDT', 'OP-USDT', 'IOTX-USDT', 'QNT-USDT', 'RAD-USDT', 'ETC-USDT', 'ANKR-USDT', 'EGLD-USDT', 'OCEAN-USDT',
            # 'LDO-USDT', 'ENS-USDT', 'MASK-USDT', 'XTZ-USDT', 'IOST-USDT', 'UNFI-USDT', 'RVN-USDT', 'RDNT-USDT', 'ZEC-USDT', 'COTI-USDT',
            # 'TRX-USDT', 'FTM-USDT', 'LINA-USDT', 'RNDR-USDT', 'HBAR-USDT', 'ICX-USDT', 'XEM-USDT', 'KAVA-USDT', 'CVX-USDT', 'UMA-USDT',
            # 'MDT-USDT', 'DODOX-USDT', 'BAL-USDT', 'AGIX-USDT', 'BLUEBIRD-USDT', 'SUSHI-USDT', 'RSR-USDT', 'GALA-USDT', 'CHZ-USDT', 'KEY-USDT',
            # 'FLM-USDT', 'AGLD-USDT', 'PERP-USDT', 'REEF-USDT', 'BAT-USDT', 'STMX-USDT', 'STG-USDT', 'FOOTBALL-USDT', 'BAND-USDT', 'XMR-USDT',
            # 'FLOW-USDT', 'DGB-USDT', '1000SHIB-USDT', 'ICP-USDT', 'ALICE-USDT', 'IOTA-USDT', 'YFI-USDT', '1000LUNC-USDT', 'ANT-USDT', 'T-USDT',
            # 'AUDIO-USDT', 'UNI-USDT', 'XRP-USDT', 'ZRX-USDT', 'MATIC-USDT', 'ONE-USDT', 'DEFI-USDT', 'MINA-USDT', 'CFX-USDT', 'CELR-USDT',
            # 'COMP-USDT', 'FET-USDT', 'JASMY-USDT', 'GAL-USDT', 'BLZ-USDT', 'XVG-USDT', 'NEAR-USDT', 'STORJ-USDT', 'SOL-USDT', 'AMB-USDT',
            # 'CTSI-USDT', 'SKL-USDT', 'WLD-USDT', 'BLUR-USDT', 'CHR-USDT', 'WOO-USDT', 'AAVE-USDT', 'AR-USDT', 'MKR-USDT', 'IMX-USDT',
            # 'YGG-USDT', 'APE-USDT', 'GMT-USDT', 'LPT-USDT', 'NKN-USDT', 'IDEX-USDT', 'HOT-USDT', 'THETA-USDT', 'DUSK-USDT', 'GRT-USDT',
            # 'XVS-USDT', 'FXS-USDT', 'WAVES-USDT', 'LIT-USDT', 'BEL-USDT', 'PENDLE-USDT', 'BNX-USDT', 'QTUM-USDT', 'CTK-USDT', 'HFT-USDT',
            # 'INJ-USDT', 'CELO-USDT', 'SNX-USDT', 'LUNA2-USDT', '1000PEPE-USDT', 'APT-USDT', 'ARPA-USDT', 'OMG-USDT', 'NMR-USDT', 'MAV-USDT',
            # 'BNB-USDT', 'XLM-USDT', 'DYDX-USDT', 'MTL-USDT', 'ATA-USDT', 'SEI-USDT', 'JOE-USDT', 'PEOPLE-USDT', 'KSM-USDT', 'LEVER-USDT',
            # 'MANA-USDT', 'ROSE-USDT', 'AXS-USDT', 'ADA-USDT', 'ACH-USDT', 'BAKE-USDT', 'HOOK-USDT', 'ETH-USDT', 'SFP-USDT', 'MAGIC-USDT',
            # 'NEO-USDT', 'VET-USDT', 'OGN-USDT', 'EOS-USDT', 'BNT-USDT', 'CRV-USDT', 'ALPHA-USDT', 'RUNE-USDT', 'ARB-USDT', 'DENT-USDT',
            # '1000XEC-USDT', 'DAR-USDT', 'AVAX-USDT', 'BCH-USDT', 'DOT-USDT', 'DASH-USDT', 'ID-USDT', 'ARKM-USDT', 'PHB-USDT', 'CKB-USDT',
            # 'KLAY-USDT', 'EDU-USDT', 'LINK-USDT', 'REN-USDT', 'KNC-USDT', 'C98-USDT', 'FIL-USDT', 'LRC-USDT', '1INCH-USDT', 'SSV-USDT',
            # 'ZEN-USDT', 'TRU-USDT', 'ASTR-USDT', 'TRB-USDT', 'ALGO-USDT', 'API3-USDT', 'LQTY-USDT', 'SPELL-USDT', 'COMBO-USDT', 'GTC-USDT',
            'GMX-USDT', 'SXP-USDT', 'LTC-USDT', 'DOGE-USDT', 'SUI-USDT'
        }
    }

    subscribed_to_order_book_trade_event = False
    prepare_ok = False

    active_buy_sell_vol = {(connector_name, asset): (0.,0.) for connector_name, assets in markets.items() for asset in assets}

    trade_list = []

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
                    conversion_rate = RateOracle.get_instance().get_pair_rate(asset)

                    self.logger().info(f"Connector: {connector_name} Asset: {asset} Mid price: {connector.get_mid_price(asset)}")
                    # self.logger().info(f"Best ask: {connector.get_price(asset, True)}")
                    # self.logger().info(f"Best bid: {connector.get_price(asset, False)}")
                    # self.logger().info(f"Mid price: {connector.get_mid_price(asset)}")
                    # self.logger().info(f"conversion_rate: {conversion_rate}")
                    # if self.is_perpetual(connector_name):
                    #     funding_rate = connector.get_funding_info(asset).rate
                    # else:
                    #     funding_rate = 0.
                    # self.logger().info(f"funding_rate: {funding_rate}")
                    #
                    # cum_activate_buy_vol, cum_activate_sell_vol = self.active_buy_sell_vol[(connector_name, asset)]
                    # self.logger().info(f"cum_activate_buy_vol: {cum_activate_buy_vol}")
                    # self.logger().info(f"cum_activate_sell_vol: {cum_activate_sell_vol}")

                    # reset the active trade volume counter
                    self.active_buy_sell_vol[(connector_name, asset)] = 0., 0.

                    for event in self.trade_list:
                        self.logger().info(f"event: {event}")
                    self.trade_list = []

                    #self.logger().info(f"#"*100)


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
        if event.type.name=="BUY":
            cum_activate_buy_vol = cum_activate_buy_vol + event.amount
        elif event.type.name=="SELL":
            cum_activate_sell_vol = cum_activate_sell_vol + event.amount
        self.active_buy_sell_vol[(connector_name, asset)] = cum_activate_buy_vol, cum_activate_sell_vol

        self.trade_list.append(event)