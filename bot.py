import os
from typing import Type

import telebot
from filters import BlueFilter, Filter, GreenFilter, InverseFilter, RedFilter
from PIL import Image
from telebot.types import KeyboardButton, ReplyKeyboardMarkup, Message


TOKEN = ''
bot = telebot.TeleBot(TOKEN)

filters: dict[str, Type[Filter]] = {
    "Красный фильтр": RedFilter(),
    "Зеленый фильтр": GreenFilter(),
    "Синий фильтр": BlueFilter(),
    "Инверсия": InverseFilter()
}

user_images = {}
images_folder = './images'

if not os.path.exists(images_folder):
    os.makedirs(images_folder)


@bot.message_handler(commands=['start'])
def handle_start(message: Message):
    print(f'{message=}')
    bot.send_message(
        message.chat.id,
        'Привет, я бот, который обрабатывает картинки. Загрузите фотку'
    )


@bot.message_handler(content_types=['photo'])
def handle_photo(message: Message):
    process_image(message)


@bot.message_handler(content_types=['text'])
def handle_text(message: Message):
    apply_filter(message)


def process_image(message: Message):
    try:
        print(message)
        file_info = bot.get_file(message.photo[-1].file_id)

        downloaded_file = bot.download_file(file_info.file_path)

        file_path = f'{images_folder}/{message.chat.id}.jpg'
        with open(file_path, 'wb') as image_file:
            image_file.write(downloaded_file)

        user_images[message.chat.id] = file_path

        keyboard = make_filter_options_keyboard(message)
        bot.send_message(message.chat.id, "Выберите фильтр:", reply_markup=keyboard)

    except Exception:
        bot.send_message(message.chat.id, 'Что-то пошло не так, попробуйте заново отправить фото')


def make_filter_options_keyboard(message: Message):
    markup = ReplyKeyboardMarkup(row_width=1)
    filters_buttons = [KeyboardButton(filt_name) for filt_name in filters.keys()]
    print(f'{filters_buttons=}')
    markup.add(*filters_buttons)
    return markup


def apply_filter(message: Message):
    file_path = user_images.get(message.chat.id)
    if not file_path:
        bot.reply_to(
            message,
            "Изображение не найдено. Пожалуйста, загрузите изображение."
        )
        return

    try:
        img = Image.open(file_path)
    except IOError:
        # Ошибка считывания файла
        bot.reply_to(
            message,
            "Формат изображения не поддерживается. Пожалуйста, загрузите другое изображение.",
        )
        return

    selected_filter_name = message.text
    if selected_filter_name not in filters:
        bot.reply_to(
            message,
            "Выбранный фильтр не найден. Пожалуйста, выберите фильтр из предложенного списка.",
        )
        return

    try:
        # Выбираем фильтр и применяем его
        selected_filter = filters[selected_filter_name]
        img = selected_filter.apply_to_image(img)

        # Сохраняем результат без создания временного файла
        img.save(file_path, "JPEG")

        with open(file_path, "rb") as image_file:
            bot.send_photo(message.chat.id, photo=image_file)
            bot.send_message(
                message.chat.id, "Ваше изображение с примененным фильтром."
            )

    except Exception as e:
        print(e)
        bot.reply_to(message,
                     "Что-то пошло не так. Пожалуйста, попробуйте еще раз.")


bot.polling()
