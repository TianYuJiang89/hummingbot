import os
import redis
import json

from hummingbot.strategy.script_strategy_base import ScriptStrategyBase


class LogPricesExample(ScriptStrategyBase):
    """
    This example shows how to get the ask and bid of a market and log it to the console.
    """
    redis_host = "localhost"
    redis_port = 6379
    # config_cache_name = "test_instance_markets_cache"
    config_cache_name = "instance_markets_cache"
    pool = redis.ConnectionPool(host=redis_host, port=redis_port, decode_responses=True)
    r = redis.Redis(connection_pool=pool)
    INSTANCE_NAME = "binance_md_1" # os.getenv("INSTANCE_NAME")
    markets = json.loads(r.hget(config_cache_name, INSTANCE_NAME))

    def on_tick(self):
        for connector_name, connector in self.connectors.items():
            for asset in self.markets[connector_name]:
                self.logger().info(f"Connector: {connector_name}")
                self.logger().info(f"asset: {asset}")
                # self.logger().info(f"Best ask: {connector.get_price(asset., True)}")
                # self.logger().info(f"Best bid: {connector.get_price(asset, False)}")
                self.logger().info(f"Mid price: {connector.get_mid_price(asset)}")
