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

        if not self.ready_to_trade:
            return

        #: check current balance of coins
        balance_df = self.get_balance_df()
        if True:
            self.logger().info("balance_df=")
            self.logger().info(balance_df.to_json(orient="records"))


        #: check active orders
        active_orders_df = self.active_orders_df()
        if True:
            self.logger().info("active_orders_df=")
            self.logger().info(active_orders_df.to_json(orient="records"))


        for connector_name, connector in self.connectors.items():
            for asset in connector.trading_pairs:
                tick_size = connector.get_order_price_quantum(asset, None)
                order_size = connector.get_order_size_quantum(asset, None)
                min_notional_size = connector.trading_rules[asset].min_notional_size

                if False:
                    self.logger().info(f"asset= {asset}")
                    self.logger().info(f"tick_size= {tick_size}")
                    self.logger().info(f"order_size= {order_size}")
                    self.logger().info(f"min_notional_size= {min_notional_size}")
