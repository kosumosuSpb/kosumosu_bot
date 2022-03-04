import json
import re
import requests
import unittest


class APIException(Exception):
    pass


# конвертер валют
class CurrencyConverter:
    """
    класс конвертера, основной метод которого принимает строку определённого формата:
    <переведи/перевод/сконвертируй> <сумма> <из чего переводить> <во что переводить>,
    и возвращает строку.

    Строка может говорить об ошибках: не верный ввод, нет такой валюты, ошибки API
    либо просто содержать результат в готовом текстовом виде:
    Если перевести {amount} {value_from} в {value_to}, будет: {conversion_result}

    """

    # список доступных валют
    CURRENCIES = {
        'доллар': 'USD',
        'евро': 'EUR',
        'биткоин': 'BTC',
        'эфириум': 'ETH',
        'рубль': 'RUR',
        'тенге': 'KZT'
    }

    # Обрабатывает запрос на конвертацию валюты, принимает текст сообщения в str
    def conversion(self, message_text: str) -> str:
        # распарсили ввод и поместили в переменные
        amount, value_from, value_to = self.parse_convert_request(message_text)

        # ищем в доступных валютах соответствие по тому что ввели (ввод может быть не корректным - долларов, рублей)
        # обратно получаем записи в корректной записи (доллар, рубль)
        base = self.search_value(value_from, self.CURRENCIES)
        quote = self.search_value(value_to, self.CURRENCIES)

        # если не нашли валюты в базе, то говорим, что нету такой
        # можно это всё через исключения сделать, но так я посчитал, что будет короче
        if not base:
            return f'Валюты такой нет у меня: {value_from}. \n' \
                   f'Список доступных валют можно узнать через команду /values'
        if not quote:
            return f'Валюты такой нет у меня: {value_to}.\n' \
                   f'Список доступных валют можно узнать через команду /values'

        # если ввели одну и ту же валюту, то говорим о бессмысленности операции
        if base == quote:
            return f'Смысла в переводе таком не вижу я. \n' \
                   f'Однако, знай, что {value_from} в {value_to} - один к одному будет переводиться'

        try:
            # запрос конвертации
            # передаём геттеру сумму, и коды валют из словаря
            conversion_result = self.get_price(amount, self.CURRENCIES[base], self.CURRENCIES[quote])
        except APIException as e:
            return f'Волнения в силе ощущаю я. Пошло не так что-то: \n{e.__cause__}'
        else:
            # возвращаем результат в чат
            return f'Если перевести {amount} {value_from} в {value_to}, будет: {conversion_result}'

    # непосредственно запрос курса валют через API и подсчёт суммы
    @staticmethod
    def get_price(amount: int, base: str, quote: str) -> float:
        """
        Простой конвертер валют на базе API cryptocompare.com

        :param amount: сумма для конвертации: int или float
        :param base: валюта из которой надо конвертировать в формате типа USD, EUR, RUR
        :param quote: валюта в которую надо конвертировать в формате типа USD, EUR, RUR
        :return: результат конвертации в float

        """
        # запрос стоимости валюты через API
        try:
            r = requests.get(f'https://min-api.cryptocompare.com/data/price?'
                             f'fsym={base}'
                             f'&tsyms={quote}')
            # смотрим через json, что пришло обратно (там будет словарь, поэтому выводим по ключу)
            conversion_result = json.loads(r.content)[quote]
        except Exception as e:
            raise APIException() from e
        else:
            # если всё ок:
            return float(conversion_result) * amount

    @staticmethod
    def parse_convert_request(text: str) -> tuple:
        """
        простой парсер для конвертера, умеет парсить формат:
        <сумма> <валюта> <валюта>
        между валютами может быть буква "в"

        :param text: что парсить
        :return:
        вернёт кортеж из трёх переменных:

        amount - сумма в float или int (если целое число),
        value_from - валюта из которой переводим в str и
        value_to - валюта, в которую переводим в str
        называются так для того, чтобы было сходу понятно даже мне
        """
        # сначала отделяем нужную нам группу текста
        pattern = re.compile(r'(?:переведи|перевод|c?конвертируй|(?:сколько будет))'
                             r'.*\s-?(\d+[.,]?\d*\s[A-Za-zА-Яа-яёЁ]{3,}\sв?\s?[A-Za-zА-Яа-яёЁ]{3,})', re.I)
        text = re.search(pattern, text)
        text = text.group(1)

        # берём отдельно число
        amount = re.search(r'\d+[.,]?\d*', text)
        # если с точкой, то делаем float, если без - то int
        amount = float(amount.group().replace(',', '.')) if re.search(r'[.,]', text) else int(amount.group())

        # отделяем то, из чего конвертируем
        value_from = re.search(r'([A-Za-zА-Яа-яёЁ]{3,})(?=\s?в?\s[A-Za-zА-Яа-яёЁ]{3,})', text)
        value_from = value_from.group(1)

        # отделяем то, во что конвертируем
        value_to = re.search(r'(?:[A-Za-zА-Яа-яёЁ]{3,}\sв?\s?)([A-Za-zА-Яа-яёЁ]{3,})', text)
        value_to = value_to.group(1)

        return amount, value_from, value_to

    @staticmethod
    def search_value(value: str, values: dict) -> str:
        """
        Простой помощник, для определения того, что за валюту ввёл пользователь
        (ввод может быть не "рубль", а "рублей", например)
        ищет по первым трём буквам в словаре с доступными валютами

        :param value: валюта, как была введена изначально
        :param values: словарь с доступными валютами
        :return: вернёт валюту в верном формате, как она записана в словаре, либо None

        """

        # берём первые три буквы в строке
        short_value = value[:3]

        # ищем в словаре соответствия и возвращаем то, с чем совпало
        for key in values.keys():
            if short_value in key:
                return key


class TestOfApps(unittest.TestCase):
    def test_conversion_requests_lowcase(self):
        test_str = 'переведи 1 доллар в рубли'
        test_return = (1, 'доллар', 'рубли')
        self.assertEqual(CurrencyConverter.parse_convert_request(test_str), test_return)

    def test_conversion_requests_capitalized(self):
        test_str = 'Переведи 1 доллар в рубли'
        test_return = (1, 'доллар', 'рубли')
        self.assertEqual(CurrencyConverter.parse_convert_request(test_str), test_return)


if __name__ == '__main__':
    unittest.main()
