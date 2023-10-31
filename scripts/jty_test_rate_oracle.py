# import functools

# from hummingbot.connector.connector_base import ConnectorBase
# from hummingbot.core.data_type.order_book import OrderBook
# from hummingbot.core.event.event_forwarder import SourceInfoEventForwarder
# from hummingbot.core.event.events import OrderBookEvent, OrderBookTradeEvent, OrderFilledEvent
from hummingbot.core.rate_oracle.rate_oracle import RateOracle
from hummingbot.strategy.script_strategy_base import ScriptStrategyBase


class TestExample(ScriptStrategyBase):
    """
    This example shows how to get the ask and bid of a market and log it to the console.
    """

    markets = {
        "gate_io_paper_trade": {"BTC-USDT"},
        # "binance": {"BTC-USDT"},
        # "binance_perpetual": {"ETH-USDT"},
        # "binance_perpetual_testnet": {"ETH-USDT"},
    }

    prepare_ok = False
    portfolio_quote = "USDT"

    def on_tick(self):
        if not self.prepare_ok:
            self.logger().info("!" * 100)
            self.logger().info("preparing!!!!!!!!!!!!!!")
            self.logger().info("!" * 100)
            self.prepare_ok = True

        if self.prepare_ok:
            self.logger().info("prepared!!!!!!!!!!!!!!")

            # for connector_name, connector in self.connectors.items():
            #     for asset in self.test_tickers:
            #         base_asset, quote_asset = asset.split("-")[0]
            #
            #
            #         conversion_rate = RateOracle.get_instance().get_pair_rate(asset)
            #         if conversion_rate is None:
            #             self.logger().info("asset: "+asset)

            # self.logger().info(f"BUSD-USDT={RateOracle.get_instance().get_pair_rate('BUSD-USDT')}")
            # self.logger().info(f"USDT-BUSD={RateOracle.get_instance().get_pair_rate('USDT-BUSD')}")
            # self.logger().info(f"USDT-USDT={RateOracle.get_instance().get_pair_rate('USDT-USDT')}")
            # self.logger().info(f"BTC-USDT={RateOracle.get_instance().get_pair_rate('BTC-USDT')}")
            # self.logger().info(f"ETH-USDT={RateOracle.get_instance().get_pair_rate('ETH-USDT')}")
            # self.logger().info(f"BTC-ETH={RateOracle.get_instance().get_pair_rate('BTC-ETH')}")
            # self.logger().info(f"ETH-BTC={RateOracle.get_instance().get_pair_rate('ETH-BTC')}")
            # self.logger().info(f"ETH-USD={RateOracle.get_instance().get_pair_rate('ETH-USD')}")
            # self.logger().info(f"USDT-USD={RateOracle.get_instance().get_pair_rate('USDT-USD')}")
            # self.logger().info(f"BUSD-USD={RateOracle.get_instance().get_pair_rate('BUSD-USD')}")
            # self.logger().info(f"ASDASDAS-USD={RateOracle.get_instance().get_pair_rate('ASDASDAS-USD')}")

            self.logger().info(f"ETH-EUR={RateOracle.get_instance().get_pair_rate('ETH-EUR')}")
            self.logger().info(f"BTC-EUR={RateOracle.get_instance().get_pair_rate('BTC-EUR')}")
            self.logger().info(f"ETH-USDT={RateOracle.get_instance().get_pair_rate('ETH-USDT')}")
            self.logger().info(f"BTC-USDT={RateOracle.get_instance().get_pair_rate('BTC-USDT')}")
            self.logger().info(f"ETH-USD={RateOracle.get_instance().get_pair_rate('ETH-USD')}")
            self.logger().info(f"BTC-USD={RateOracle.get_instance().get_pair_rate('BTC-USD')}")
            self.logger().info(f"USDT-USD={RateOracle.get_instance().get_pair_rate('USDT-USD')}")
            self.logger().info(f"BUSD-USD={RateOracle.get_instance().get_pair_rate('BUSD-USD')}")
