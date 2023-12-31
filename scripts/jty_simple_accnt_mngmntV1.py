from hummingbot.strategy.script_strategy_base import ScriptStrategyBase

import os
import redis
import orjson as json

class SimpleAccountManager(ScriptStrategyBase):
    ######################################################################################################
    # Begin: Redis Settings
    ######################################################################################################
    # redis_host = "localhost"
    redis_host = "localhost"# os.getenv("CONFIG_HOST_IP")
    redis_port = 6379

    config_cache_name = "instance_markets_cache"

    pool = redis.ConnectionPool(host=redis_host, port=redis_port, decode_responses=True)
    r = redis.Redis(connection_pool=pool)

    ######################################################################################################
    # End: Redis Settings
    ######################################################################################################

    ######################################################################################################
    # Begin: Account Manage Range Settings
    ######################################################################################################
    # To configure which exchange/ticker need to be record
    INSTANCE_NAME = "accnt_mngmnt" # os.getenv("CONFIG_INSTANCE_ID")
    markets = json.loads(r.hget(config_cache_name, INSTANCE_NAME))

    ######################################################################################################
    # End: RAccount Manage Settings
    ######################################################################################################

    def on_tick(self):
        pass