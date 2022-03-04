from instagrapi import Client
from bot_config import INST_LOGIN, INST_PASS
from datetime import datetime
import logging
import os


"""
Обёртка для instagrapi, сделана для расширения функционала, 
например, отслеживания того, кто подписался и отписался за какой-то период 

пока всё заточено под локальную работу и не привязано к боту

Базируется на instagrapi
https://github.com/adw0rd/instagrapi

для начала работы необходимо залогиниться 
(также в instagrapi есть возможность работы через прокси 
и с двухфакторной авторизацией, но здесь простой пример):

inst = InstaClient()
inst.login(login, password)

по-умолчанию ищет их в константах INST_LOGIN и INST_PASS

что умеет:
* снимать дамп id подписчиков по введённому имени пользователя и сохранять локально в файл
- [в процессе] показ разницы между двумя дампами
- кеширование в файл
- кеширование через редис
- возможность скачать файл из бота
- хранение данных в sqLite/MySQL
- частичное кеширование в БД?
- докер

"""

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class InstaClient(Client):
    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)
        self._user_kasmas = 'kasmas'  # чтобы сто раз не вводить свой ник

    # user_id = inst.user_id_from_username(user)
    # username = username_from_user_id(user_id: int) - в обратную сторону

    @staticmethod
    def create_and_login(login=INST_LOGIN, password=INST_PASS):
        instance = InstaClient()
        instance.login(login, password)
        return instance

    def save_followers(self, user: int or str):
        """Сохранение id подписчиков в файл"""
        if isinstance(user, str):
            user_id = self.user_id_from_username(user)
        else:
            user_id = user

        # получаем список подписчиков
        followers = self.user_followers(user_id)

        # проверяем наличие папки под файлы, если нету - создаём
        if not os.path.isdir('inst'):
            logger.info('Cant find inst directory, creating it...')
            os.mkdir('inst')

        # записываем в файл
        now = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        with open(f'inst/{user}_followers_{now}.txt', 'w') as f:
            for s in followers:
                f.write(s+'\n')

    def followers_changes(self, user, show_id=False):
        """Сравнить последний и предпоследний файлы и показать разницу"""
        # найти два последних файла для введённого пользователя
        # открыть оба, найти разницу
        # если её нет - то закончить
        # если есть - вывести разницу
        # если show_id=True - показать id, вместо юзернеймов

