from hummingbot.core.rate_oracle.rate_oracle import RateOracle
from hummingbot.strategy.script_strategy_base import ScriptStrategyBase
#from hummingbot.connector.connector_base import ConnectorBase
from hummingbot.core.data_type.order_book import OrderBook
from hummingbot.core.event.event_forwarder import SourceInfoEventForwarder
from hummingbot.core.event.events import OrderBookEvent, OrderBookTradeEvent, OrderFilledEvent

import functools

class TestExample(ScriptStrategyBase):
    """
    This example shows how to get the ask and bid of a market and log it to the console.
    """
    """
    markets = {

        "binance": {"BTC-USDT"},
        # "binance_perpetual": {"ETH-USDT"},
        # "binance_perpetual_testnet": {"ETH-USDT"},
    }
    """


    markets = {
        'binance_perpetual': {
            'TLM-USDT', 'CYBER-USDT', 'HIGH-USDT', 'ZIL-USDT', 'SAND-USDT', 'RLC-USDT', 'ENJ-USDT',
            'STX-USDT', 'ATOM-USDT', 'OXT-USDT', 'TOMO-USDT', 'ONT-USDT', 'OP-USDT', 'IOTX-USDT',
            'QNT-USDT', 'RAD-USDT', 'ETC-USDT', 'ANKR-USDT', 'EGLD-USDT', 'OCEAN-USDT', 'LDO-USDT',
            'ENS-USDT', 'MASK-USDT', 'XTZ-USDT', 'IOST-USDT', 'UNFI-USDT', 'RVN-USDT', 'RDNT-USDT',
            'ZEC-USDT', 'COTI-USDT', 'TRX-USDT', 'FTM-USDT', 'LINA-USDT', 'RNDR-USDT', 'HBAR-USDT',
            'ICX-USDT', 'XEM-USDT', 'KAVA-USDT', 'CVX-USDT', 'UMA-USDT', 'MDT-USDT', 'DODOX-USDT',
            'BAL-USDT', 'AGIX-USDT', 'BLUEBIRD-USDT', 'SUSHI-USDT', 'RSR-USDT', 'GALA-USDT',
            'CHZ-USDT', 'KEY-USDT', 'FLM-USDT', 'AGLD-USDT', 'PERP-USDT', 'REEF-USDT', 'BAT-USDT',
            'STMX-USDT', 'STG-USDT', 'FOOTBALL-USDT', 'BAND-USDT', 'XMR-USDT', 'FLOW-USDT',
            'DGB-USDT', '1000SHIB-USDT', 'ICP-USDT', 'ALICE-USDT', 'IOTA-USDT', 'YFI-USDT',
            '1000LUNC-USDT', 'ANT-USDT', 'T-USDT', 'AUDIO-USDT', 'UNI-USDT', 'XRP-USDT', 'ZRX-USDT',
            'MATIC-USDT', 'ONE-USDT', 'DEFI-USDT', 'MINA-USDT', 'CFX-USDT', 'CELR-USDT', 'COMP-USDT',
            'FET-USDT', 'JASMY-USDT', 'GAL-USDT', 'BLZ-USDT', 'XVG-USDT', 'NEAR-USDT', 'STORJ-USDT',
            'SOL-USDT', 'AMB-USDT', 'CTSI-USDT', 'SKL-USDT', 'WLD-USDT', 'BLUR-USDT', 'CHR-USDT',
            'WOO-USDT', 'AAVE-USDT', 'AR-USDT', 'MKR-USDT', 'IMX-USDT', 'YGG-USDT', 'APE-USDT',
            'GMT-USDT', 'LPT-USDT', 'NKN-USDT', 'IDEX-USDT', 'HOT-USDT', 'THETA-USDT', 'DUSK-USDT',
            'GRT-USDT', 'XVS-USDT', 'FXS-USDT', 'WAVES-USDT', 'LIT-USDT', 'BEL-USDT', 'PENDLE-USDT',
            'BNX-USDT', 'QTUM-USDT', 'CTK-USDT', 'HFT-USDT', 'INJ-USDT', 'CELO-USDT', 'SNX-USDT',
            'LUNA2-USDT', '1000PEPE-USDT', 'APT-USDT', 'ARPA-USDT', 'OMG-USDT', 'NMR-USDT',
            'MAV-USDT', 'BNB-USDT', 'XLM-USDT', 'DYDX-USDT', 'MTL-USDT', 'ATA-USDT', 'SEI-USDT',
            'JOE-USDT', 'PEOPLE-USDT', 'KSM-USDT', 'LEVER-USDT', 'MANA-USDT', 'ROSE-USDT', 'AXS-USDT',
            'ADA-USDT', 'ACH-USDT', 'BAKE-USDT', 'HOOK-USDT', 'ETH-USDT', 'SFP-USDT', 'MAGIC-USDT',
            'NEO-USDT', 'VET-USDT', 'OGN-USDT', 'EOS-USDT', 'BNT-USDT', 'CRV-USDT', 'ALPHA-USDT',
            'RUNE-USDT', 'ARB-USDT', 'DENT-USDT', '1000XEC-USDT', 'DAR-USDT', 'AVAX-USDT', 'BCH-USDT',
            'DOT-USDT', 'DASH-USDT', 'ID-USDT', 'ARKM-USDT', 'PHB-USDT', 'CKB-USDT', 'KLAY-USDT',
            'EDU-USDT', 'LINK-USDT', 'REN-USDT', 'KNC-USDT', 'C98-USDT', 'FIL-USDT', 'LRC-USDT',
            '1INCH-USDT', 'SSV-USDT', 'ZEN-USDT', 'TRU-USDT', 'ASTR-USDT', 'TRB-USDT', 'ALGO-USDT',
            'API3-USDT', 'LQTY-USDT', 'SPELL-USDT', 'COMBO-USDT', 'GTC-USDT', 'GMX-USDT', 'SXP-USDT',
            'LTC-USDT', 'DOGE-USDT', 'SUI-USDT'
        }
    }

    prepare_ok = False

    def on_tick(self):
        if not self.prepare_ok:
            self.logger().info("!"*100)
            self.logger().info("preparing!!!!!!!!!!!!!!")
            self.logger().info("!" * 100)
            self.prepare_ok = True

        if self.prepare_ok:
            self.logger().info("prepared!!!!!!!!!!!!!!")
