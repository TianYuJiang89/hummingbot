from hummingbot.strategy.script_strategy_base import ScriptStrategyBase
from hummingbot.core.data_type.common import OrderType
from hummingbot.connector.derivative.position import Position

from typing import Dict, List
from decimal import Decimal
import pandas as pd
import numpy as np

class TestAcountInfo(ScriptStrategyBase):

    # gate_io_paper_trade
    # binance_perpetual
    # binance
    # binance_perpetual_paper_trade
    # binance_perpetual_testnet
    test_exchange = "binance_perpetual_testnet"
    markets = {
        test_exchange: [
            "BTC-USDT",
            #"ETH-USDT",
            #"ETH-BTC",
            "XRP-USDT",
            "TRX-USDT",
        ]
    }

    had_buy = False

    def on_tick(self):

        if not self.ready_to_trade:
            return

        #: check current balance of coins
        balance_df = self.get_balance_df()
        if True:
            self.logger().info("\nbalance_df=")
            # self.logger().info(f"\n{balance_df}")
            self.logger().info(balance_df.to_json(orient="records"))

            # [
            # {"exchange": "binance_perpetual_testnet", "ticker": "BTC", "total_balance": 0.0, "available_balance":0.0},
            # {"exchange":"binance_perpetual_testnet","ticker":"TRX","total_balance":0.0,"available_balance":0.0},
            # {"exchange": "binance_perpetual_testnet", "ticker": "USDT", "total_balance": 14999.4472103, "available_balance": 14986.7951903},
            # {"exchange": "binance_perpetual_testnet", "ticker": "XRP", "total_balance": 0.0, "available_balance": 0.0}
            # ]

        #: check active orders
        active_orders_df = self.active_orders_df()
        if True:
            self.logger().info("\nactive_orders_df=")
            # self.logger().info(f"\n{active_orders_df}")
            self.logger().info(active_orders_df.to_json(orient="records"))

            # [{"exchange":"binance_perpetual_testnet","ticker":"BTC-USDT","side":"buy","price":30000.0,"amount":0.007,"age":"00:01:06"}]

        #: check active position
        active_positions_df = self.active_positions_df()
        if True:
            self.logger().info("\nactive_positions_df=")
            # self.logger().info(f"\n{active_positions_df}")
            self.logger().info(active_positions_df.to_json(orient="records"))

            # [{"exchange": "binance_perpetual_testnet", "ticker": "BTC-USDT", "price": 43090.4, "amount":-0.003,"leverage":20.0,"unrealized_pnl":-5.8332}]


        if not self.had_buy:
            # self.buy(
            #     connector_name=self.test_exchange,
            #     trading_pair="BTC-USDT",
            #     amount=Decimal(0.003),
            #     order_type=OrderType.LIMIT,
            #     price=Decimal(50000)
            # )

            # self.sell(
            #     connector_name=self.test_exchange,
            #     trading_pair="BTC-USDT",
            #     amount=Decimal(0.012),
            #     order_type=OrderType.LIMIT,
            #     price=Decimal(40000)
            # )

            self.buy(
                connector_name=self.test_exchange,
                trading_pair="BTC-USDT",
                amount=Decimal(0.007),
                order_type=OrderType.LIMIT,
                price=Decimal(30000)
            )

            self.had_buy = True


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

    def get_balance_df(self) -> pd.DataFrame:
        """
        Returns a data frame for all asset balances for displaying purpose.
        """
        columns = ["exchange", "ticker", "total_balance", "available_balance"]
        data = []
        for connector_name, connector in self.connectors.items():
            for asset in self.get_assets(connector_name):
                data.append([connector_name,
                             asset,
                             float(connector.get_balance(asset)),
                             float(connector.get_available_balance(asset))])
        df = pd.DataFrame(data=data, columns=columns).replace(np.nan, '', regex=True)
        df.sort_values(by=["exchange", "ticker"], inplace=True)
        return df

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

        return df

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

