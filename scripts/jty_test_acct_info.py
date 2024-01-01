from hummingbot.strategy.script_strategy_base import ScriptStrategyBase
from hummingbot.core.data_type.common import OrderType

from decimal import Decimal
import pandas as pd

class TestAcountInfo(ScriptStrategyBase):

    # gate_io_paper_trade
    # binance_perpetual
    # binance
    # binance_perpetual_paper_trade
    # binance_perpetual_testnet
    markets = {
        "binance_perpetual_testnet": [
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
            self.logger().info(balance_df)
            # self.logger().info(balance_df.to_json(orient="records"))


        #: check active orders
        active_orders_df = self.active_orders_df()
        if True:
            self.logger().info("\nactive_orders_df=")
            self.logger().info(active_orders_df)
            # self.logger().info(active_orders_df.to_json(orient="records"))

        if not self.had_buy:
            self.buy(
                connector_name="kucoin_paper_trade",
                trading_pair="BTC-USDT",
                amount=Decimal(0.003),
                order_type=OrderType.LIMIT,
                price=Decimal(50000)
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

    def active_orders_df(self) -> pd.DataFrame:
        """
        Return a data frame of all active orders for displaying purpose.
        """
        columns = ["Exchange", "Market", "Side", "Price", "Amount", "Age"]
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
        df.sort_values(by=["Exchange", "Market", "Side"], inplace=True)
        return df