import peewee
import telebot

from loader import bot, UserRequest
from api_requests import get_destination_id, get_hotels_info
from peewee import Model


def get_city(message: telebot.types.Message, request_id: str) -> None:
    user_request = UserRequest.get_by_id(request_id)
    city = message.text
    user_request.city = city
    user_request.save()

    if not get_destination_id(city,
                              user_request):
        bot.send_message(message.from_user.id,
                         "Не получается найти такой город."
                         "Проверьте правильность ввода, "
                         "затем попробуйте ввести заново")
        bot.register_next_step_handler(message,
                                       get_city,
                                       request_id)
        return

    bot.send_message(message.from_user.id,
                     "Сколько отелей показать? ")
    bot.register_next_step_handler(message,
                                   get_hotels_count,
                                   user_request)


def get_hotels_count(message: telebot.types.Message, request_data: Model) -> None:
    try:
        count = int(message.text)
        request_data.hotels_count = count
        request_data.save()
    except ValueError:
        bot.send_message(message.from_user.id,
                         'Укажите, пожалуйста, количество в числовом формате')
        bot.register_next_step_handler(message,
                                       get_hotels_count,
                                       request_data)
        return

    need_photos_keyboard = telebot.types.InlineKeyboardMarkup()

    key_yes = telebot.types.InlineKeyboardButton('Да',
                                                 callback_data='yes')
    need_photos_keyboard.add(key_yes)
    key_no = telebot.types.InlineKeyboardButton('Нет',
                                                callback_data='no')
    need_photos_keyboard.add(key_no)

    bot.send_message(message.from_user.id,
                     text='Показать фотографии отелей? ',
                     reply_markup=need_photos_keyboard)


@bot.callback_query_handler(func=lambda call: True)
def does_need_photos(call: telebot.types.CallbackQuery) -> None:
    user_request = UserRequest.select()\
        .where(UserRequest.user_id == call.message.chat.id)\
        .order_by(UserRequest.id.desc())\
        .get_or_none()

    if call.data == 'yes':
        bot.send_message(call.message.chat.id,
                         'Сколько показать фотографий?\n(не более 4-х)')
        bot.register_next_step_handler(call.message,
                                       get_photos_count, user_request)
    elif call.data == 'no':
        bot.send_message(call.message.chat.id,
                         'Минутку')
        get_hotels_info(call.message.chat.id, user_request)


def get_photos_count(message: telebot.types.Message, request_data: peewee.Model) -> None:

    photos_count = int(message.text)

    if 1 > photos_count > 4:
        bot.send_message(message.from_user.id,
                         'Укажите, пожалуйста, число от 1 до 4')
        bot.register_next_step_handler(message,
                                       get_photos_count)
        return

    request_data.photos_count = photos_count
    request_data.save()
    bot.send_message(message.from_user.id,
                     'Минутку')

    get_hotels_info(message.chat.id, request_data)
