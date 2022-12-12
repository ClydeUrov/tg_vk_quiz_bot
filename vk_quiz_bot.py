import os
import random
import vk_api
from dotenv import load_dotenv
from telegram.ext import CallbackContext
import redis
import logging
import time

from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from get_sentences import get_quiz


def send_messages(event, vk, text):
    vk.messages.send(
        user_id=event.user_id,
        message=text,
        keyboard=keyboard.get_keyboard(),
        random_id=random.randint(1,1000),
    )


def handle_new_question_request(event, vk):
    global question_number, total_questions
    total_questions += 1
    question_number += 2
    send_messages(event, vk, get_quiz()[question_number])
    redis_db.set(event.user_id, get_quiz()[question_number])
    for key in redis_db.scan_iter():
        h = redis_db.get(key)
        print(h)
    print(redis_db.keys())
    print(get_quiz()[question_number + 1])


def handle_solution_attempt(event, vk):
    global question_number, correct_answers
    if event.text in get_quiz()[question_number + 1]:
        correct_answers += 1
        send_messages(event, vk, "Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос»")
    else:
        send_messages(event, vk, "Неправильно… Попробуешь ещё раз?")


def take_surrender(event, vk):
    global question_number, surrender
    surrender += 1
    send_messages(event, vk, f'К сожалению вы сдались.. Правильный ответ:\n{get_quiz()[question_number + 1]}\nЧтобы продолжить, нажмите "Новый вопрос"')


def view_score(update, context: CallbackContext):
    global total_questions, correct_answers, surrender
    send_messages(event, vk, f'Всего вопросов: {total_questions}\nПравильных ответов: {correct_answers}\nПотерпели неудач: {surrender}')


if __name__ == '__main__':
    load_dotenv()

    question_number, total_questions, correct_answers, surrender = 0,0,0,0    
    redis_db = redis.Redis(
        host=os.environ["REDIS_HOST"], 
        port=os.environ["REDIS_PORT"], 
        password=os.environ["REDIS_PASWORD"],
        decode_responses=True,
    )
    print(redis_db.keys())
    vk_session = vk_api.VkApi(token=os.environ["VK_TOKEN"])
    vk = vk_session.get_api()

    keyboard = VkKeyboard(one_time=True)

    keyboard.add_button('Новый вопрос', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('Сдаться', color=VkKeyboardColor.NEGATIVE)
    keyboard.add_line()
    keyboard.add_button('Мой счёт', color=VkKeyboardColor.POSITIVE)

    while True:
        try:
            longpoll = VkLongPoll(vk_session)
            for event in longpoll.listen():
                if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                    if event.text == 'Start':
                        print(event.text)
                        send_messages(event, vk, "Привет! Начнём викторину?")
                    elif event.text == "Новый вопрос":
                        handle_new_question_request(event, vk)
                    elif event.text == 'Сдаться':
                        take_surrender(event, vk)
                    elif event.text == 'Мой счёт':
                        view_score(event, vk)
                    else:
                        handle_solution_attempt(event, vk)
        except Exception:
            logging.exception('VK бот упал с ошибкой: ')
            time.sleep(10)
