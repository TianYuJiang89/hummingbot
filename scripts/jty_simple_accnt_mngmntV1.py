from hummingbot.strategy.script_strategy_base import ScriptStrategyBase

import os
import redis
import orjson as json
import pandas as pd

class SimpleAccountManager(ScriptStrategyBase):
    ######################################################################################################
    # Begin: Redis Settings
    ######################################################################################################
    # redis_host = "localhost"
    redis_host = "localhost"# os.getenv("CONFIG_HOST_IP")
    redis_port = 6379

    config_cache_name = "instance_markets_cache" # to initialize the market variable
    cmd2acc_cache_name = "cmd2acc" # receive order instruction from commander script
    cmd2acc_heartbeat_cache_name = "cmd2acc_lastupddttm"
    acc2cmd_cache_name = "acc2cmd"  # receive order instruction from commander script
    acc2cmd_heartbeat_cache_name = "acc2cmd_lastupddttm"


    pool = redis.ConnectionPool(host=redis_host, port=redis_port, decode_responses=True)
    r = redis.Redis(connection_pool=pool)

    ######################################################################################################
    # End: Redis Settings
    ######################################################################################################

    ######################################################################################################
    # Begin: Account Manage Range Settings
    ######################################################################################################
    # To configure which exchange/ticker need to be record
    INSTANCE_NAME = "accnt_mngmnt_1" # os.getenv("CONFIG_INSTANCE_ID")
    # markets = json.loads(r.hget(config_cache_name, INSTANCE_NAME))

    test_exchange = "binance_perpetual_testnet"
    markets = {
        test_exchange: [
            "BTC-USDT",
            # "ETH-USDT",
            # "ETH-BTC",
            "XRP-USDT",
            "TRX-USDT",
        ]
    }

    ######################################################################################################
    # End: Account Manage Settings
    ######################################################################################################

    ######################################################################################################
    # Begin: Internal variables
    ######################################################################################################
    _all_markets_ready = False

    ######################################################################################################
    # End: Internal variables
    ######################################################################################################

    def on_tick(self):
        if self._all_markets_ready == False:
            self.logger().warning("Markets are not ready. No trades are permitted.")
            self._all_markets_ready = self.all_markets_ready()
        else:

            # account balance info
            balance_df = self.get_balance_df()
            balance_dict = balance_df.to_json(orient="records")

            # active orders info
            active_orders_df = self.active_orders_df()
            active_orders_dict = active_orders_df.to_json(orient="records")

            # active positions info
            active_positions_df = self.active_positions_df()
            active_positions_dict = active_positions_df.to_json(orient="records")

            # INSTANCE_NAME

    def all_markets_ready(self):
        return all([market.ready for market in self.active_markets])

    def active_orders_df(self) -> pd.DataFrame:
        """
        Return a data frame of all active orders for displaying purpose.
        """
        columns = ["exchange", "ticker", "side", "price", "amount", "age"]
        data = []
        for connector_name, connector in self.connectors.items():
            for order in self.get_active_orders(connector_name):
                age_txt = "n/a" if order.age() <= 0. else pd.Timestamp(order.age(), unit='s').strftime('%H:%M:%S')
                data.append([
                    connector_name,
                    order.trading_pair,
                    "buy" if order.is_buy else "sell",
                    float(order.price),
                    float(order.quantity),
                    age_txt
                ])

        # if not data:
        #     raise ValueError
        df = pd.DataFrame(data=data, columns=columns)
        df.sort_values(by=["exchange", "ticker", "side"], inplace=True)

    def active_positions_df(self) -> pd.DataFrame:
        columns = ["exchange", "ticker", "price", "amount", "leverage", "unrealized_pnl"]
        data = []
        for connector_name, connector in self.connectors.items():
            for position in connector.account_positions.values():
                data.append([
                    connector_name,
                    position.trading_pair,
                    position.entry_price,
                    position.amount,
                    position.leverage,
                    position.unrealized_pnl,
                ])

        df = pd.DataFrame(data=data, columns=columns)
        df.sort_values(by=["exchange", "ticker"], inplace=True)

        return df