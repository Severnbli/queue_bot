from aiogram.types import ReplyKeyboardMarkup


class Message:
    def __init__(self, user_id: int, text: str, is_check_news: bool, markup: ReplyKeyboardMarkup = None):
        self.__user_id: int = user_id
        self.__text: str = text
        self.__markup: ReplyKeyboardMarkup = markup
        self.__is_check_news: bool = is_check_news

    async def get_user_id(self) -> int:
        return self.__user_id

    async def get_text(self) -> str:
        return self.__text

    async def get_markup(self) -> ReplyKeyboardMarkup:
        return self.__markup

    async def is_check_news(self) -> bool:
        return self.__is_check_news

    async def set_user_id(self, user_id: int) -> None:
        self.__user_id = user_id

    async def set_text(self, text: str) -> None:
        self.__text = text

    async def set_markup(self, markup: ReplyKeyboardMarkup) -> None:
        self.__markup = markup

    async def set_is_check_news(self, is_check_news: bool) -> None:
        self.__is_check_news = is_check_news