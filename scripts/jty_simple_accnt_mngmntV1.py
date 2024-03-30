from hummingbot.core.data_type.limit_order import LimitOrder

from hummingbot.core.data_type.common import PositionAction
from hummingbot.strategy.script_strategy_base import ScriptStrategyBase
from hummingbot.core.data_type.common import OrderType
from decimal import Decimal
import os
import redis
import orjson as json
# import pandas as pd
from datetime import datetime, timezone
import time

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
    # INSTANCE_NAME = "accnt_mngmnt_1" # os.getenv("CONFIG_INSTANCE_ID")
    INSTANCE_NAME = "accnt_mngmnt_testnet"
    markets = json.loads(r.hget(config_cache_name, INSTANCE_NAME))

    ######################################################################################################
    # End: Account Manage Settings
    ######################################################################################################

    ######################################################################################################
    # Begin: Internal variables
    ######################################################################################################
    _all_markets_ready = False

    last_instruction_lastupddttm = 0.
    ######################################################################################################
    # End: Internal variables
    ######################################################################################################

    def on_tick(self):
        if not self._all_markets_ready:
            self.logger().warning("Markets are not ready. No trades are permitted.")
            self._all_markets_ready = self.all_markets_ready()
            if self._all_markets_ready:
                self.logger().warning("Markets are ready!!!")
        else:
            ######################################################################################################
            # Begin: Receive order instruction from commander script, and send order
            ######################################################################################################
            instruction_lastupddttm = self.r.hget(self.cmd2acc_heartbeat_cache_name, self.INSTANCE_NAME)
            if self.last_instruction_lastupddttm != instruction_lastupddttm:
                self.last_instruction_lastupddttm = instruction_lastupddttm

                # batch cancel orders
                for connector_name, connector in self.connectors.items():
                    orders_to_cancel = self.get_active_orders(connector_name)
                    connector.batch_order_cancel(
                        orders_to_cancel=orders_to_cancel,
                    )

                # batch create orders
                # instruction_list_dict sample
                # {
                #   'ready2trade': True,
                #   'connector_instruction_list': {
                #       'binance_perpetual_testnet': [
                #           {
                #               'ticker': 'BTC-USDT',
                #               'side': 'B',
                #               'base_ccy': 'BTC',
                #               'quote_ccy': 'USDT',
                #               'price': 30000.1,
                #               'qty': 0.5
                #           }
                #       ],
                #       'binance_perpetual': [
                #           {
                #               'ticker': 'ETH-USDT',
                #               'side': 'S',
                #               'base_ccy': 'ETH',
                #               'quote_ccy': 'USDT',
                #               'price': 4000.1,
                #               'qty': 0.3
                #           }
                #       ]
                #   }
                # }

                instruction_list_dict_str = self.r.hget(self.cmd2acc_cache_name, self.INSTANCE_NAME)
                if instruction_list_dict_str is not None:
                    instruction_list_dict = json.loads(instruction_list_dict_str)
                    ready2trade = instruction_list_dict["ready2trade"]
                    if ready2trade:

                        for connector_name, connector in self.connectors.items():

                            instruction_list = instruction_list_dict["connector_instruction_list"][connector_name]
                            # orders_to_create = []
                            for instruction in instruction_list:
                                ticker = instruction["ticker"]
                                is_buy = True if instruction["side"]=="B" else False
                                # base_ccy = instruction["base_ccy"]
                                # quote_ccy = instruction["quote_ccy"]
                                price = instruction["price"]
                                qty = instruction["qty"]

                                if is_buy:
                                    self.buy(
                                        connector_name=connector_name,
                                        trading_pair=ticker,
                                        amount=Decimal(qty),
                                        order_type=OrderType.LIMIT,
                                        price=Decimal(price)
                                    )
                                else:
                                    self.sell(
                                        connector_name=connector_name,
                                        trading_pair=ticker,
                                        amount=Decimal(qty),
                                        order_type=OrderType.LIMIT,
                                        price=Decimal(price)
                                    )

                                # to avoid the 300 orders per 10s limit
                                time.sleep(0.034)

                                # order = LimitOrder(
                                #     client_order_id="",
                                #     trading_pair=ticker,
                                #     is_buy=is_buy,
                                #     base_currency=base_ccy,
                                #     quote_currency=quote_ccy,
                                #     price=price,
                                #     quantity=qty,
                                # )
                                # orders_to_create.append(order)

                            # submitted_orders = connector.batch_order_create(
                            #     orders_to_create=orders_to_create,
                            # )

            ######################################################################################################
            # End: Receive order instruction from commander script, and send order
            ######################################################################################################

            ######################################################################################################
            # Begin: Send data to commander script
            ######################################################################################################
            acc_info = dict()
            # account balance info
            balance_data_list = self.get_balance_info()
            acc_info["balance_data_list"] = balance_data_list

            # active orders info
            active_orders_data_list = self.get_active_orders_info()
            acc_info["active_orders_data_list"] = active_orders_data_list

            # active positions info
            active_positions_data_list = self.get_active_positions_info()
            acc_info["active_positions_data_list"] = active_positions_data_list

            utcnow_stamp = datetime.now(tz=timezone.utc).timestamp()

            self.r.hset(self.acc2cmd_cache_name, self.INSTANCE_NAME, json.dumps(acc_info))
            self.r.hset(self.acc2cmd_heartbeat_cache_name, self.INSTANCE_NAME, utcnow_stamp)
            ######################################################################################################
            # End: Send data to commander script
            ######################################################################################################

    def all_markets_ready(self):
        return all([market.ready for market in self.active_markets])

    def get_balance_info(self):
        """
        Returns a data frame for all asset balances for displaying purpose.
        """
        data_list = []
        for connector_name, connector in self.connectors.items():
            for asset in self.get_assets(connector_name):
                data = dict()
                data["exchange"] = connector_name
                data["ticker"] = asset
                data["total_balance"] = float(connector.get_balance(asset))
                data["available_balance"] = float(connector.get_available_balance(asset))
                data_list.append(data)

        return data_list

    def get_active_orders_info(self):
        data_list = []
        for connector_name, connector in self.connectors.items():
            for order in self.get_active_orders(connector_name):
                data = dict()
                data["exchange"] = connector_name
                data["ticker"] = order.trading_pair
                data["side"] = "B" if order.is_buy else "S",
                data["price"] = float(order.price)
                data["qty"] = float(order.quantity)
                data["age"] = float(order.age() )
                data_list.append(data)

        return data_list

    def get_active_positions_info(self):
        data_list = []
        for connector_name, connector in self.connectors.items():
            for position in connector.account_positions.values():
                data = dict()
                data["exchange"] = connector_name
                data["ticker"] = position.trading_pair
                data["price"] = float(position.entry_price)
                data["qty"] = float(position.amount)
                data["leverage"] = float(position.leverage)
                data["unrealized_pnl"] = float(position.unrealized_pnl)
                data_list.append(data)

        return data_list
