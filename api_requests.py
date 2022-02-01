import json
import peewee
import requests

from loader import bot, HEADERS, SORT_ORDER, get_hotel_data_from_json


def get_destination_id(city: str, user_request: str) -> bool:
    url = "https://hotels4.p.rapidapi.com/locations/v2/search"
    querystring = {
        "query": city,
        "locale": "ru_RU",
        "currency": "RUB"
    }

    response = requests.request("GET",
                                url,
                                headers=HEADERS,
                                params=querystring)
    response_dict = json.loads(response.text)

    try:
        suggestions = response_dict.get("suggestions")
        entities = suggestions[0].get("entities")
        destination_id = entities[0].get("destinationId")
        user_request.destination_id = destination_id
        return True

    except IndexError:
        return False


def get_hotels_info(chat_id: int, user_request: peewee.Model) -> None:
    url = "https://hotels4.p.rapidapi.com/properties/list"
    sort_order = SORT_ORDER[user_request.command]

    querystring = {
        "destinationId": user_request.destination_id,
        "pageNumber": "1",
        "pageSize": str(user_request.hotels_count),
        "checkIn": user_request.check_in,
        "checkOut": user_request.check_out,
        "adults1": "1",
        "sortOrder": sort_order,
        "locale": "ru_RU",
        "currency": "RUB",
    }

    response = requests.request("GET",
                                url,
                                headers=HEADERS,
                                params=querystring)

    send_final_result(chat_id, response.text, user_request)


def send_final_result(chat_id: int, full_response: str, user_request: peewee.Model) -> None:
    hotels = tuple(hotel for hotel in get_hotel_data_from_json(full_response, user_request))

    for hotel in hotels:
        if user_request.photos_count is not None:
            send_hotel_photos(chat_id,
                              hotel.hotel_id,
                              user_request.photos_count)
        send_hotel_info(chat_id, hotel)


def send_hotel_info(chat_id: int, hotel: peewee.Model) -> None:

    cur_hotel_info = f"{hotel.name}\n" \
                     f"\u2605{hotel.rating}\n" \
                     f"Адрес: {hotel.address}\n" \
                     f"Расстояние до центра города: {hotel.distance_to_center}\n" \
                     f"Цена: {hotel.price}\n" \
                     f"{hotel.hotel_url}"

    bot.send_message(chat_id, cur_hotel_info)


def send_hotel_photos(chat_id: int, hotel_id: str, count: int) -> None:
    url = "https://hotels4.p.rapidapi.com/properties/get-hotel-photos"

    querystring = {"id": hotel_id}
    response = requests.request("GET",
                                url,
                                headers=HEADERS,
                                params=querystring)

    photos = json.loads(response.text).get("hotelImages")
    size = 'y'
    photos_sent = 0

    for photo_info in photos:
        if photos_sent >= count:
            break

        photo_url_raw: str = photo_info.get("baseUrl")
        photo_url = photo_url_raw.replace("{size}", size)
        bot.send_photo(chat_id, photo_url)
        photos_sent += 1
