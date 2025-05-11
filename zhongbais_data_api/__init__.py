from zhongbais_data_api.entry import get_dat


class zbDataAPI(object):
    @staticmethod
    def register_player_info_callback(
        func,
        list = []
    ) -> None:
        """
        注册回调函数，按照Config中的刷新时间配置，触发回调

        Register callback function, configure according to the refresh time in Config, and trigger callback

        Args:
            func (callable): 回调函数，接收参数 (name: str, info: dict)

                             The callback function, receives (name: str, info: dict)

            list (list): 需要监听的玩家列表，默认为空，表示监听所有NBT

                         The list of players to listen to, default is empty, meaning listen to all NBT

        Returns:
            None
        """
        get_dat.register_player_info_callback(list, func)

    @staticmethod
    def get_player_list() -> list:
        """
        获取在线玩家列表

        Get the list of online players

        Returns:
            list: 玩家列表 / List of player names
        """
        return get_dat.player_list.copy()

    @staticmethod
    def register_player_list_callback(func) -> None:
        """
        注册回调函数，在玩家列表增减时触发

        Register a callback, triggered when the player list changes

        Args:
            func (callable): 回调函数，接收参数 (player_list: list)

                             The callback function, receives (player_list: list)

        Returns:
            None
        """
        get_dat.register_player_list_callback(func)

    @staticmethod
    def refresh_getpos() -> None:
        """
        手动刷新 player_info

        Manually refresh player_info

        Returns:
            None
        """
        get_dat.manual_fetch()
