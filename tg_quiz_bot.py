import argparse
import logging
import os
import time

import redis
import telegram
from dotenv import load_dotenv
from telegram.ext import (CallbackContext, CommandHandler, ConversationHandler,
                          Filters, MessageHandler, RegexHandler, Updater)

from get_sentences import get_quiz


def start(update, context):
    reply_markup = context.bot_data['reply_markup']
    update.message.reply_text(
        text="Привет! Я бот для викторин!", reply_markup=reply_markup
    )
    user = str(update.message.chat_id)
    redis_db.hset("user" + user, "question_number", 0)
    redis_db.hset("user" + user, "total_questions", 0)
    redis_db.hset("user" + user, "correct_answers", 0)
    redis_db.hset("user" + user, "surrender", 0)
    return NEW_QUESTION


def handle_new_question_request(update, context):
    user = str(update.message.chat_id)
    quiz = context.bot_data['quiz']
    reply_markup = context.bot_data['reply_markup']

    total_questions = int(redis_db.hget("user" + user, "total_questions"))
    total_questions += 1
    redis_db.hset("user" + user, "total_questions", total_questions)

    question_number = int(redis_db.hget("user" + user, "question_number"))
    update.message.reply_text(text=quiz[question_number], reply_markup=reply_markup)
    question_number += 2
    redis_db.hset("user" + user, "question_number", question_number)
    return TYPING_REPLY


def handle_solution_attempt(update, context: CallbackContext):
    user = str(update.message.chat_id)
    quiz = context.bot_data['quiz']
    reply_markup = context.bot_data['reply_markup']
    question_number = int(redis_db.hget("user" + user, "question_number"))

    if update.message.text in quiz[question_number - 1]:
        update.message.reply_text(
            "Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос»",
            reply_markup=reply_markup,
        )
        correct_answers = int(redis_db.hget("user" + user, "correct_answers"))
        correct_answers += 1
        redis_db.hset("user" + user, "correct_answers", correct_answers)
        return NEW_QUESTION
    else:
        update.message.reply_text(
            "Неправильно… Попробуешь ещё раз?", reply_markup=reply_markup
        )
        return TYPING_REPLY


def take_surrender(update, context):
    user = str(update.message.chat_id)
    quiz = context.bot_data['quiz']
    question_number = int(redis_db.hget("user" + user, "question_number"))

    update.message.reply_text(
        f'Пфф, слабак.. Правильный ответ:\n{quiz[question_number - 1]}\nЧтобы продолжить, нажмите "Новый вопрос"'
    )
    surrender = int(redis_db.hget("user" + user, "surrender"))
    surrender += 1
    redis_db.hset("user" + user, "surrender", surrender)
    return NEW_QUESTION


def view_score(update, context):
    user = str(update.message.chat_id)
    total_questions = redis_db.hget("user" + user, "total_questions")
    correct_answers = redis_db.hget("user" + user, "correct_answers")
    surrender = redis_db.hget("user" + user, "surrender")
    update.message.reply_text(
        f"Всего вопросов: {total_questions}\nПравильных ответов: {correct_answers}\nПотерпели неудач: {surrender}"
    )


def error_callback(update, context):
    logging.warning('Update "%s" caused error "%s"', update, context.error)


def stop(update, context):
    update.message.reply_text("Программа завершена.")
    return ConversationHandler.END


if __name__ == "__main__":
    load_dotenv()
    parser = argparse.ArgumentParser(description="Проводит викторину в TG.")
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
    NEW_QUESTION, TYPING_REPLY, SURRENDER = range(3)
    updater = Updater(os.environ["TG_TOKEN"], use_context=True)
    custom_keyboard = [["Новый вопрос", "Сдаться"], ["Мой счёт"]]
    reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)

    dp = updater.dispatcher
    dp.bot_data['reply_markup'] = reply_markup
    dp.bot_data['quiz'] = quiz

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NEW_QUESTION: [
                RegexHandler("^Новый вопрос$", handle_new_question_request),
                RegexHandler("^Мой счёт$", view_score),
            ],
            TYPING_REPLY: [
                RegexHandler("^Сдаться$", take_surrender),
                RegexHandler("^Мой счёт$", view_score),
                MessageHandler(
                    Filters.text, handle_solution_attempt, pass_user_data=True
                ),
            ],
        },
        fallbacks=[CommandHandler("stop", stop)],
    )
    dp.add_handler(conv_handler)
    dp.add_error_handler(error_callback)
    updater.start_polling()
    updater.idle()
