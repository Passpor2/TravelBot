import telebot
import os
import peewee
import json

from collections.abc import Iterable
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

HEADERS = {
    "x-rapidapi-host": "hotels4.p.rapidapi.com",
    f"x-rapidapi-key": RAPIDAPI_KEY
}

SORT_ORDER = {
    "/lowprice": "PRICE",
    "/highprice": "PRICE_HIGHEST_FIRST",
}

bot = telebot.TeleBot(TOKEN)
db = peewee.SqliteDatabase("hotels.sqlite")


class UserRequest(peewee.Model):
    user_id = peewee.IntegerField()
    command = peewee.CharField()
    request_dt = peewee.DateTimeField()
    check_in = peewee.DateField()
    check_out = peewee.DateField()
    city = peewee.CharField(null=True)
    destination_id = peewee.CharField(null=True)
    hotels_count = peewee.IntegerField(null=True)
    photos_count = peewee.IntegerField(null=True)

    class Meta:
        database = db


class HotelData(peewee.Model):
    request_id = peewee.ForeignKeyField(UserRequest,
                                        verbose_name="hotels")
    hotel_id = peewee.CharField()
    name = peewee.CharField()
    rating = peewee.CharField()
    address = peewee.CharField(null=True)
    distance_to_center = peewee.CharField(null=True)
    price = peewee.CharField()
    hotel_url = peewee.CharField()

    class Meta:
        database = db


def get_hotel_data_from_json(full_data: str, user_request: peewee.Model) -> Iterable:
    response_dict = json.loads(full_data)
    data = response_dict.get("data")
    body = data.get("body")
    search_results = body.get("searchResults")
    results = search_results.get("results")

    for hotel in results:
        hotel_id = hotel.get("id")
        name = hotel.get("name")
        star_rating = hotel.get("starRating")
        address = hotel.get("address").get("streetAddress")
        landmarks = hotel.get("landmarks")
        distance_to_center = None
        price = hotel.get("ratePlan").get("price").get("current")
        url = f"https://ru.hotels.com/ho{hotel_id}/?q-check-in={user_request.check_in}" \
              f"&q-check-out={user_request.check_out}&q-rooms=1&q-room-0-adults=1&q-room-0-children=0"

        for landmark in landmarks:
            label = landmark.get("label").lower()
            if "центр" in label or "center" in label:
                distance_to_center = landmark.get("distance")

        new_hotel_data = HotelData.create(
            request_id=user_request.get_id(),
            hotel_id=hotel_id,
            name=name,
            rating=star_rating,
            address=address,
            distance_to_center=distance_to_center,
            price=price,
            hotel_url=url
        )

        yield new_hotel_data


if not UserRequest.table_exists():
    UserRequest.create_table()

if not HotelData.table_exists():
    HotelData.create_table()
