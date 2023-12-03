import os
from pyignite import Client
from pyignite.datatypes import MapObject
import json

from hummingbot.strategy.script_strategy_base import ScriptStrategyBase


class LogPricesExample(ScriptStrategyBase):
    """
    This example shows how to get the ask and bid of a market and log it to the console.
    """
    ignite_host = "127.0.0.1"
    ignite_port = 10800
    config_cache_name = "test_config_cache"
    client = Client()
    client.connect(ignite_host, ignite_port)
    config_cache = client.get_or_create_cache(config_cache_name)
    _, instance_id_market_dict = config_cache.get("instance_id_market_dict")

    INSTANCE_NAME = os.getenv("INSTANCE_NAME")
    markets = json.loads(instance_id_market_dict[INSTANCE_NAME])

    def on_tick(self):
        for connector_name, connector in self.connectors.items():
            for asset in self.markets[connector_name]:
                self.logger().info(f"Connector: {connector_name}")
                self.logger().info(f"asset: {asset}")
                # self.logger().info(f"Best ask: {connector.get_price(asset., True)}")
                # self.logger().info(f"Best bid: {connector.get_price(asset, False)}")
                self.logger().info(f"Mid price: {connector.get_mid_price(asset)}")
