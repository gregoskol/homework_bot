import logging
import os
import sys
import time
from http import HTTPStatus
from logging import StreamHandler

import requests
from dotenv import load_dotenv
from telegram import Bot

from exceptions import SendMessageError

load_dotenv()
PRACTICUM_TOKEN = os.getenv("PRACTICUM_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

FIRST_TIME_DELTA = 86400
RETRY_TIME = 600
ENDPOINT = "https://practicum.yandex.ru/api/user_api/homework_statuses/"
HEADERS = {"Authorization": f"OAuth {PRACTICUM_TOKEN}"}


HOMEWORK_VERDICTS = {
    "approved": "Работа проверена: ревьюеру всё понравилось. Ура!",
    "reviewing": "Работа взята на проверку ревьюером.",
    "rejected": "Работа проверена: у ревьюера есть замечания.",
}


def send_message(bot, message):
    """Отправка сообщения в Telegram."""
    try:
        logger.info("Отправка сообщения в Telegram...")
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
        )
    except Exception as error:
        raise SendMessageError(message, error)
    else:
        logger.info("Сообщение успешно отправлено.")


def get_api_answer(current_timestamp):
    """Запрос к эндпоинту Практикум.Домашка.
    Возвращает ответ API в формате JSON
    """
    timestamp = current_timestamp or int(time.time())
    params = {"from_date": timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except Exception as error:
        raise Exception(f"Ошибка при запросе к API: {error}")
    if response.status_code != HTTPStatus.OK:
        raise Exception(
            f"Сбой в работе программы: Эндпоинт {ENDPOINT}"
            f" недоступен. Код ответа API: {response.status_code}"
        )
    return response.json()


def check_response(response):
    """Проверка ответа от API на корректность.
    Возвращает список домашних работ.
    """
    if type(response) is not dict:
        raise TypeError("Ответ от API имеет некорректный формат")
    if type(response["homeworks"]) is not list:
        raise TypeError(
            "Ответ от API имеет некорректный формат по ключу 'homeworks'"
        )
    if "homeworks" not in response:
        raise KeyError("Отсутствует ключ 'homework' в ответе API")
    if "current_date" not in response:
        raise KeyError("Отсутствует ключ 'current_date' в ответе API")
    if len(response["homeworks"]) > 0:
        return response.get("homeworks")
    else:
        logger.debug("В ответе от API нет домашних работ")


def parse_status(homework):
    """Получение информации о последней работе.
    Формирование сообщения со статусом проверки.
    """
    homework_name = homework["homework_name"]
    homework_status = homework["status"]
    try:
        verdict = HOMEWORK_VERDICTS[homework_status]
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    except KeyError:
        raise KeyError("Статус работы не найден в словаре HOMEWORK_VERDICTS")


def check_tokens():
    """Проверка доступности переменных окружения.
    Возвращает True, если все переменные доступны.
    """
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


#    Максим, привет! Но ведь в примере в ТЗ лог содержит название
#    конкретной недоступной переменной, а так мы его не получим
#    tokens = {
#        PRACTICUM_TOKEN: "PRACTICUM_TOKEN",
#        TELEGRAM_TOKEN: "TELEGRAM_TOKEN",
#        TELEGRAM_CHAT_ID: "TELEGRAM_CHAT_ID",
#    }
#    for value in tokens:
#        if value is None:
#            logger.critical(
#                "Отсутствует обязательная переменная окружения: "
#                f"{tokens[value]}. Программа принудительно остановлена."
#            )
#            return False
#    return True


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logger.critical(
            "Отсутствует обязательная переменная окружения."
            "Программа принудительно остановлена."
        )
        sys.exit()
    message_status = ""
    message_error = ""
    bot = Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time()) - FIRST_TIME_DELTA
    while True:
        try:
            response = get_api_answer(current_timestamp)
            current_timestamp = response.get("current_date")
            checked_response = check_response(response)
            if checked_response is not None:
                message = parse_status(checked_response[0])
                if message != message_status:
                    send_message(bot, message)
                    message_status = message
                else:
                    logger.debug("Статус работы не изменился")
                time.sleep(RETRY_TIME)
        except Exception as error:
            logger.error(error)
            message = f"Сбой в работе программы: {error}"
            if message != message_error:
                send_message(bot, message)
                message_error = message
        finally:
            time.sleep(RETRY_TIME)


if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    handler = StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] func:%(funcName)s"
        " line:%(lineno)d %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    main()
