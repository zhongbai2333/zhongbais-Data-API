from mcdreforged.api.all import Serializable

class Config(Serializable):
    afk_time: int = 300
    refresh_data_time: int = 1
    # 机器人名称匹配规则：
    # - 支持通配符（glob）：*, ?, []，例如："bot_*", "*_bot", "Bot??Bot*"
    # - 如果不包含通配符，则退回到“子串包含”的旧行为，例如："bot_" 会匹配所有包含 "bot_" 的名字
    # 注意：匹配区分大小写
    bot_keyword: str = "bot_"
    debug: bool = False
