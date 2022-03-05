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
        if instance.login(login, password):
            logger.info(f'Пользователь {login} авторизован успешно')
            return instance
        else:
            logger.info(f'Авторизовать пользователя {login} не удалось')

    def save_followers(self, user: int or str):
        """Сохранение id подписчиков в файл"""
        if isinstance(user, str):
            logger.info(f'Получаем id пользователя {user}...')
            user_id = self.user_id_from_username(user)
        else:
            user_id = user

        # получаем список подписчиков
        logger.info(f'Получаем подписчиков пользователя {user}...')
        followers = self.user_followers(user_id)

        # проверяем наличие папки под файлы, если нету - создаём
        if not os.path.isdir('inst'):
            logger.info('Cant find inst directory, creating it...')
            os.mkdir('inst')

        # записываем в файл
        now = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        counter = 0
        with open(f'inst/{user}_followers_{now}.txt', 'w+') as f:
            for s in followers:
                f.write(s+'\n')
                counter += 1

        logger.info(f'Сохранено {counter} подписчиков')

    def followers_changes(self, user, show_id=False):
        """Сравнить последний и предпоследний файлы и показать разницу"""
        # получаем список файлов в папке inst
        files = os.listdir(path="./inst")
        logger.info(f'Файлы: {files}')
        files = sorted([file for file in files if file[:len(user)] == user])  # берём только нужный юзернейм и сортируем
        f2, f1 = files[-2:]  # берём последние два - самые поздние

        logger.info(f'Берём два последних файла: {f2}, {f1}')

        # читаем оба файла. Получим два списка вида ['49520889582\n', '51507879495\n', '50037477495\n', ... ]
        # перевод строки потом надо не забыть убрать
        logger.info('Открываем оба файла...')
        with open(f'inst/{f2}') as file2, open(f'inst/{f1}') as file1:
            f2 = file2.readlines()
            f1 = file1.readlines()

        # находим разницу в файлах
        difference = set(f1).symmetric_difference(f2)
        logger.debug(f'Получившееся множество: {difference}')

        if not difference:
            print('Изменений в подписчиках нет')
            return False

        # эти - подписались (потому что их нет в старом файле)
        new = [follower[:-1] for follower in difference if follower not in f2]
        new = self.get_usernames(new) if not show_id else new

        # эти - отписались (потому что их нет в новом)
        gone = [follower[:-1] for follower in difference if follower not in f1]
        gone = self.get_usernames(gone) if not show_id else gone

        print(f'Подписались: {new}\n'
              f'Отписались: {gone}')

    def get_usernames(self, user_ids: list) -> list:
        """Принимает список id, возвращает список юзернеймов"""
        return [self.username_from_user_id(user_id) for user_id in user_ids]

    def take_file_dump(self):
        """Принимает файл дампа подписчиков"""
