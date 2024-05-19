from hummingbot.strategy.script_strategy_base import ScriptStrategyBase


class LogPricesExample(ScriptStrategyBase):
    """
    This example shows how to get the ask and bid of a market and log it to the console.
    """
    markets = {
        # "gate_io_paper_trade": {"ETH-USDT"},
        "binance_perpetual": {"ETH-USDT", "BTC-USDT"},
    }

    def on_tick(self):
        for connector_name, connector in self.connectors.items():
            for asset in self.markets[connector_name]:
                self.logger().info(f"Connector: {connector_name}")
                self.logger().info(f"asset: {asset}")
                # self.logger().info(f"Best ask: {connector.get_price(asset., True)}")
                # self.logger().info(f"Best bid: {connector.get_price(asset, False)}")
                self.logger().info(f"Mid price: {connector.get_mid_price(asset)}")

                if self.is_perpetual(connector_name):
                    funding_rate = connector.get_funding_info(asset).rate
                    next_funding_utc_timestamp = connector.get_funding_info(asset).next_funding_utc_timestamp
                else:
                    funding_rate = 0.
                    next_funding_utc_timestamp = None

                self.logger().info(f"funding_rate: {funding_rate}")
                self.logger().info(f"next_funding_utc_timestamp: {next_funding_utc_timestamp}")