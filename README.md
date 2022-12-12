# Бот для викторин в VK и Телеграм.
  
![gif](example.gif)


### Запуск программы
  
Переменные окружения

Создайте файл `.env` в корневой папке с кодом и запишите туда:
```
TG_TOKEN=ВАШ_TELEGRAM_API_КЛЮЧ
REDIS_HOST=ВАШ_REDIS_HOST
REDIS_PASWORD=ВАШ_REDIS_PASWORD
REDIS_PORT=ВАШ_REDIS_PORT
VK_TOKEN=ВАШ_API_КЛЮЧ_ВК
```

Для запуска у вас уже должен быть установлен [Python 3](https://www.python.org/downloads/release/python-379/).

- Скачайте код.
- Установите зависимости командой:
```
pip install -r requirements.txt
```
- Запустите скрипт командой: 
```
python vk_quiz_bot.py
```
```
python tg_quiz_bot.py
```
Нажимаем `/start`. Пользуемся!



### Цель проекта

Код написан в образовательных целях на онлайн-курсе для веб-разработчиков [dvmn.org](https://dvmn.org/).
 