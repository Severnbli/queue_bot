class Message:
    def __init__(self, user_id: int, text: str, is_check_news: bool):
        self.__user_id: int = user_id
        self.__text: str = text
        self.__is_check_news: bool = is_check_news

    def get_user_id(self) -> int:
        return self.__user_id

    def get_text(self) -> str:
        return self.__text

    def is_check_news(self) -> bool:
        return self.__is_check_news

    def set_user_id(self, user_id: int) -> None:
        self.__user_id = user_id

    def set_text(self, text: str) -> None:
        self.__text = text

    def set_is_check_news(self, is_check_news: bool) -> None:
        self.__is_check_news = is_check_news