import telebot
import datetime
import handlers

from loader import bot, UserRequest


@bot.message_handler(content_types=["text"])
def get_msg(message: telebot.types.Message) -> None:
    text = message.text

    if text.lower() in ("/hello-world", "привет", "/help", "help"):
        response = "Привет. " \
                   "\nЭтот телеграмм-бот поможет найти подходящие отели в любом городе мира." \
                   "\n\nКоманды бота:" \
                   "\n/lowprice: самые дешёвые отели в выбранном городе" \
                   "\n/highprice: самые дорогие отели" \
                   "\n/bestdeal: отели в заданном ценовом диапазоне, " \
                   "находящиеся от центра города не далее заданного расстояния" \
                   "\n/history: история запросов"
        bot.send_message(message.from_user.id, response)

    elif text in ("/lowprice", "/highprice"):
        today = datetime.datetime.now()
        check_in = (today + datetime.timedelta(1)).date()
        check_out = (today + datetime.timedelta(2)).date()
        user_request = UserRequest(user_id=message.from_user.id,
                                   command=text,
                                   request_dt=datetime.datetime.now(),
                                   check_in=check_in,
                                   check_out=check_out)
        user_request.save()
        bot.send_message(message.from_user.id, "Введите город: ")
        bot.register_next_step_handler(message,
                                       handlers.get_city,
                                       user_request.get_id())

    else:
        bot.send_message(message.from_user.id,
                         'Извините, но такую команду бот не поддерживает. '
                         'Воспользуйтесь командой /help или введите '
                         '"Привет" для получения информации о боте.')


if __name__ == '__main__':
    bot.polling(none_stop=True, interval=0, timeout=50)
