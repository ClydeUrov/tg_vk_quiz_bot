import argparse
import logging
import os
import random
import time

import redis
import vk_api
from dotenv import load_dotenv
from telegram.ext import CallbackContext
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.longpoll import VkEventType, VkLongPoll

from get_sentences import get_quiz


def send_messages(event, vk, text):
    vk.messages.send(
        user_id=event.user_id,
        message=text,
        keyboard=keyboard.get_keyboard(),
        random_id=random.randint(1, 1000),
    )


def handle_new_question_request(event, vk):
    total_questions = int(redis_db.hget("user" + event.user_id, "total_questions"))
    question_number = int(redis_db.hget("user" + event.user_id, "question_number"))
    total_questions += 1
    question_number += 2
    redis_db.hset("user" + event.user_id, "total_questions", total_questions)
    redis_db.hset("user" + event.user_id, "question_number", question_number)
    send_messages(event, vk, quiz[question_number])


def handle_solution_attempt(event, vk):
    question_number = int(redis_db.hget("user" + event.user_id, "question_number"))
    if event.text in quiz[question_number - 1]:
        correct_answers = int(redis_db.hget("user" + event.user_id, "correct_answers"))
        correct_answers += 1
        redis_db.hset("user" + event.user_id, "correct_answers", correct_answers)
        send_messages(
            event,
            vk,
            "Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос»",
        )
    else:
        send_messages(event, vk, "Неправильно… Попробуешь ещё раз?")


def take_surrender(event, vk):
    question_number = int(redis_db.hget("user" + event.user_id, "question_number"))
    surrender = int(redis_db.hget("user" + event.user_id, "surrender"))
    surrender += 1
    redis_db.hset("user" + event.user_id, "surrender", surrender)
    send_messages(
        event,
        vk,
        f'К сожалению вы сдались.. Правильный ответ:\n{quiz[question_number - 1]}\nЧтобы продолжить, нажмите "Новый вопрос"',
    )


def view_score(update, context: CallbackContext):
    total_questions = redis_db.hget("user" + event.user_id, "total_questions")
    correct_answers = redis_db.hget("user" + event.user_id, "correct_answers")
    surrender = redis_db.hget("user" + event.user_id, "surrender")
    send_messages(
        event,
        vk,
        f"Всего вопросов: {total_questions}\nПравильных ответов: {correct_answers}\nПотерпели неудач: {surrender}",
    )


if __name__ == "__main__":
    load_dotenv()
    parser = argparse.ArgumentParser(description="Проводит викторину в VK")
    parser.add_argument(
        "-f",
        dest="file_path",
        help="Путь к файлу с вопросами",
        default="questions/1vs1200.txt",
    )
    redis_db = redis.Redis(
        host=os.environ["REDIS_HOST"],
        port=os.environ["REDIS_PORT"],
        password=os.environ["REDIS_PASWORD"],
        decode_responses=True,
    )

    quiz = get_quiz(parser.parse_args().file_path)
    vk_session = vk_api.VkApi(token=os.environ["VK_TOKEN"])
    vk = vk_session.get_api()

    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button("Новый вопрос", color=VkKeyboardColor.PRIMARY)
    keyboard.add_button("Сдаться", color=VkKeyboardColor.NEGATIVE)
    keyboard.add_line()
    keyboard.add_button("Мой счёт", color=VkKeyboardColor.POSITIVE)

    while True:
        try:
            longpoll = VkLongPoll(vk_session)
            for event in longpoll.listen():
                if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                    if event.text == "Start":
                        redis_db.hset("user" + event.user_id, "question_number", 0)
                        redis_db.hset("user" + event.user_id, "total_questions", 0)
                        redis_db.hset("user" + event.user_id, "correct_answers", 0)
                        redis_db.hset("user" + event.user_id, "surrender", 0)
                        send_messages(event, vk, "Привет! Начнём викторину?")
                    elif event.text == "Новый вопрос":
                        handle_new_question_request(event, vk)
                    elif event.text == "Сдаться":
                        take_surrender(event, vk)
                    elif event.text == "Мой счёт":
                        view_score(event, vk)
                    else:
                        handle_solution_attempt(event, vk)
        except Exception:
            logging.exception("VK бот упал с ошибкой: ")
            time.sleep(10)
