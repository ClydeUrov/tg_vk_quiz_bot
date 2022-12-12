import logging
import os
import time
import redis
import telegram
from dotenv import load_dotenv
from telegram.ext import (CallbackContext, CommandHandler, ConversationHandler,
                          Filters, MessageHandler, RegexHandler, Updater)

from get_sentences import get_quiz


def start(update, context: CallbackContext):
    update.message.reply_text(
        text="Привет! Я бот для викторин!", reply_markup=reply_markup
    )
    return NEW_QUESTION


def handle_new_question_request(update, context: CallbackContext):
    global question_number, total_questions
    total_questions += 1
    question_number += 2
    update.message.reply_text(text=get_quiz()[question_number], reply_markup=reply_markup)
    redis_db.set(update.message.chat_id, get_quiz()[question_number])
    return TYPING_REPLY


def handle_solution_attempt(update, context: CallbackContext):
    global question_number, correct_answers
    if update.message.text in get_quiz()[question_number + 1]:
        correct_answers += 1
        update.message.reply_text(
            "Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос»",
            reply_markup=reply_markup,
        )
        return NEW_QUESTION
    else:
        update.message.reply_text(
            "Неправильно… Попробуешь ещё раз?", reply_markup=reply_markup
        )
        return TYPING_REPLY


def take_surrender(update, context: CallbackContext):
    global question_number, surrender
    surrender += 1
    update.message.reply_text(
        f'К сожалению вы сдались.. Правильный ответ:\n{get_quiz()[question_number + 1]}\nЧтобы продолжить, нажмите "Новый вопрос"'
    )
    return NEW_QUESTION


def view_score(update, context: CallbackContext):
    global total_questions, correct_answers, surrender
    update.message.reply_text(f'Всего вопросов: {total_questions}\nПравильных ответов: {correct_answers}\nПотерпели неудач: {surrender}')


def error(update, error):
    logging.warning('Update "%s" caused error "%s"', update, error)


def stop(update, context: CallbackContext):
    global question_number, total_questions, correct_answers, surrender
    update.message.reply_text("Программа завершена.")
    question_number = total_questions = correct_answers = surrender = 0
    return ConversationHandler.END


if __name__ == "__main__":
    load_dotenv()

    redis_db = redis.StrictRedis(
        host=os.environ["REDIS_HOST"],
        port=os.environ["REDIS_PORT"],
        password=os.environ["REDIS_PASWORD"],
        charset="utf-8",
        decode_responses=True,
    )

    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
        level=logging.INFO
    )

    NEW_QUESTION, TYPING_REPLY, SURRENDER = range(3)
    question_number = total_questions = correct_answers = surrender = 0

    custom_keyboard = [["Новый вопрос", "Сдаться"], ["Мой счёт"]]
    reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)

    updater = Updater(os.environ["TG_TOKEN"])
    dp = updater.dispatcher

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
    dp.add_error_handler(error)
    try:
        updater.start_polling()
        updater.idle()
    except Exception:
        logging.exception('Телеграмм бот упал с ошибкой: ')
        time.sleep(10)
