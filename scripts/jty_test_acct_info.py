from hummingbot.strategy.script_strategy_base import ScriptStrategyBase
class TestAcountInfo(ScriptStrategyBase):

    # gate_io_paper_trade
    # binance_perpetual
    # binance
    # binance_perpetual_paper_trade
    markets = {
        "binance_perpetual": [
            "BTC-USDT",
            #"ETH-USDT",
            #"ETH-BTC",
            "XRP-USDT",
            "TRX-USDT",
        ]
    }

    def on_tick(self):
        #: check current balance of coins
        # balance_df = self.get_balance_df()
        # self.logger().info(f"Tbalance_df= {balance_df}")

        for connector_name, connector in self.connectors.items():
            for asset in connector.trading_pairs:
                self.logger().info(f"asset= {asset}")

                tick_size = connector.get_order_price_quantum(asset, None)
                self.logger().info(f"tick_size= {tick_size}")

                order_size = connector.get_order_size_quantum(asset, None)
                self.logger().info(f"order_size= {order_size}")
