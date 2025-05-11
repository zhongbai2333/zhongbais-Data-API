from mcdreforged.api.all import Serializable

class Config(Serializable):
    afk_time: int = 300
    refresh_data_time: int = 1
    bot_prefix: str = "bot_"
    debug: bool = False
