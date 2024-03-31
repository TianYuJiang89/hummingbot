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

    ######################################################################################################
    # Begin: order execution related variables
    ######################################################################################################
    orders_per_clock_time = 20 # per 3 sec
    is_executing = False
    executing_segment = 0
    last_segment = 0

    orders_to_cancel_dict = dict()
    orders_to_exec_list_dict = dict()
    ready2trade = False
    ######################################################################################################
    # End: order execution related variables
    ######################################################################################################

    def on_tick(self):
        if not self._all_markets_ready:
            self.logger().warning("Markets are not ready. No trades are permitted.")
            self._all_markets_ready = self.all_markets_ready()
            if self._all_markets_ready:
                self.logger().warning("Markets are ready!!!")
        else:
            ######################################################################################################
            # Begin: Receive order instruction from commander script, and save to temporary variables
            ######################################################################################################
            instruction_lastupddttm = self.r.hget(self.cmd2acc_heartbeat_cache_name, self.INSTANCE_NAME)
            if self.last_instruction_lastupddttm != instruction_lastupddttm:
                self.last_instruction_lastupddttm = instruction_lastupddttm

                orders_to_cancel_dict = dict()
                for connector_name, connector in self.connectors.items():
                    orders_to_cancel = self.get_active_orders(connector_name)
                    orders_to_cancel_dict.update({(connector_name, order.trading_pair, order.is_buy): order.client_order_id for order in orders_to_cancel})


                instruction_list_dict_str = self.r.hget(self.cmd2acc_cache_name, self.INSTANCE_NAME)
                if instruction_list_dict_str is not None:
                    instruction_list_dict = json.loads(instruction_list_dict_str)
                    ready2trade = instruction_list_dict["ready2trade"]
                    self.ready2trade = ready2trade

                    orders_to_exec_list_dict = dict()
                    for connector_name, connector in self.connectors.items():
                        instruction_list = instruction_list_dict["connector_instruction_list"][connector_name]
                        orders_to_exec_list_dict[connector_name] = instruction_list
                    self.is_executing = True
                    self.executing_segment = 0
            ######################################################################################################
            # End: Receive order instruction from commander script, and save to temporary variables
            ######################################################################################################

            ######################################################################################################
            # Begin: Send order from temporary variables
            ######################################################################################################
            if self.is_executing:
                segment_bgn = self.executing_segment * self.orders_per_clock_time
                segment_end = (self.executing_segment + 1) * self.orders_per_clock_time

                is_exec_done = True
                for connector_name, connector in self.connectors.items():
                    orders_to_cancel_dict = self.orders_to_cancel_dict
                    instruction_list = self.orders_to_exec_list_dict[connector_name]

                    for instruction in instruction_list[segment_bgn: segment_end]:
                        ticker = instruction["ticker"]
                        is_buy = True if instruction["side"] == "B" else False
                        # base_ccy = instruction["base_ccy"]
                        # quote_ccy = instruction["quote_ccy"]
                        price = instruction["price"]
                        qty = instruction["qty"]

                        if (connector_name, ticker, is_buy) in orders_to_cancel_dict:
                            cancel_order_id = orders_to_cancel_dict[(connector_name, ticker, is_buy)]
                            if self.ready2trade:
                                self.cancel(
                                    connector_name=connector_name,
                                    trading_pair=ticker,
                                    order_id=cancel_order_id,
                                )

                        if self.ready2trade:
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

                        is_exec_done = False

                self.executing_segment = self.executing_segment + 1

                if is_exec_done:
                    self.is_executing = False
                    self.executing_segment = 0
            ######################################################################################################
            # End: Send order from temporary variables
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
