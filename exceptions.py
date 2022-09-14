class SendMessageError(Exception):
    def __init__(self, *args):
        if args:
            self.message = args[0]
            self.error = args[1]
        else:
            self.message = None

    def __str__(self):
        if self.message:
            return (
                f"Сообщение '{self.message}' не удалось отправить "
                f"по причине ошибки: {self.error}"
            )
        else:
            return "Исключение SendMessageError вызвано без аргументов"
