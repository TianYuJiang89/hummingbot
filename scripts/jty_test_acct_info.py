from hummingbot.strategy.script_strategy_base import ScriptStrategyBase
class TestAcountInfo(ScriptStrategyBase):

    # gate_io_paper_trade
    # binance_perpetual

    markets = {
        "binance_perpetual": [
            "BTC-USDT"
        ]
    }

    def on_tick(self):
        #: check current balance of coins
        balance_df = self.get_balance_df()

        self.logger().info(f"Tbalance_df= {balance_df}")

