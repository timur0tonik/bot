from flask import Flask, request
import logging
import json
from function import send_notification, get_user_by_id

app = Flask(__name__)

# настройка логирования
logging.basicConfig(filename='flask_app.log', level=logging.DEBUG)
logger = logging.getLogger(__name__)

@app.route('/jira', methods=['POST'])
def jira_webhook():
    data = request.json
    logger.debug(f'Received data: {json.dumps(data)}') # Записать данные в лог-файл в виде JSON
    if 'webhookEvent' in data and data['webhookEvent'] == 'comment_created':
        comment = data['comment']['body']
        user_id = data['comment']['author']['key']
        user_data = get_user_by_id(user_id) # получаем данные пользователя по user_id
        if user_data:
            message = f"Новый комментарий в задаче: {comment}"
            logging.debug(f"Received new comment: {comment}")
            logging.debug(f"Comment author ID: {user_id}")
            logging.debug(f"User data: {user_data}")
            send_notification(user_data, message) # отправляем уведомление пользователю
            # добавляем запись в лог-файл
            logging.debug(f"Новый комментарий в задаче: {comment}. Пользователь: {user_id}")
            logging.debug(f"Отправлено уведомление пользователю: {user_data['user_id']}")
        else:
            logging.debug(f"Не удалось получить данные пользователя для user_id: {user_id}")
    return 'OK'

# создание дополнительного обработчика логов Flask
if not app.debug:
    import logging
    from logging.handlers import RotatingFileHandler
    file_handler = RotatingFileHandler('flask_app.log', maxBytes=1024 * 1024 * 100, backupCount=20)
    file_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)
    app.logger.addHandler(file_handler)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)

