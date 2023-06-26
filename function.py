import sqlite3
import requests
from ldap3 import Server, Connection, SIMPLE, SYNC, ASYNC, SUBTREE, ALL
import settings as var
from jira import JIRA, Comment #Подключение модуля для работы с Jira Api
import telebot
import logging

logging.basicConfig(filename='send_notification.log', level=logging.DEBUG)
logger = logging.getLogger(__name__)

my_bot = telebot.TeleBot(var.botToken)
my_bott = var.botToken
JIRA_SERVER = var.server
JIRA_USER = var.jira_login
JIRA_PASS = var.jira_password

jira = JIRA(JIRA_SERVER, basic_auth=(JIRA_USER, JIRA_PASS))

def jira_login():
    try:
        return jira
    except:
        return "Error login"

def create_ticket_jira(summary_text, fullname, user, descr_text):
    jira = jira_login()
    if jira == "Error login":
        return False
    issue = jira.create_issue(fields={
        'project': {'key': 'HD'},
        'issuetype': {'name': 'Задача'},
        'reporter': {'name': user},
        'summary': summary_text,
        'description': descr_text,
    })
    return issue.key

def add_comment_to_jira_ticket(issue_key: str, comment_text: str, session=None):
    try:
        issue = jira.issue(issue_key)
        jira.add_comment(issue, comment_text)

        # Отправка уведомления в Telegram
        user_id = issue.fields.reporter.accountId
        print(f"Sending notification to user {user_id}: {comment_text}")
        send_notification(user_id, comment_text)

        return True
    except Exception as e:
        print(f"Failed to add comment to jira ticket {issue_key}: {str(e)}")

        # Обработка возможной ошибки при отправке уведомления в Telegram
        try:
            send_notification(user_id, f"Failed to add comment to jira ticket {issue_key}")
        except:
            pass

        return False

def chat_id_search(chat_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE chat_id=?", (chat_id,))
    row = cursor.fetchone()
    if row:
        return True
    cursor.close()

def add_user_base(user):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (chat_id, first_name, last_name, ad_user) VALUES (?, ?, ?, ?)", user)
    conn.commit()
    conn.close()

def user_fullname_search(chat_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE chat_id=?", (chat_id,))
    row = cursor.fetchone()
    if row:
        return row[2] + ' ' + row[1]
    cursor.close()

def get_user_by_id(user_id):
    # Получение пользователя по user_id из базы данных SQLite
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE ad_user=?", (user_id,))
    row = cursor.fetchone()
    if row:
        user = {
            "chat_id": row[0],
            "first_name": row[1],
            "last_name": row[2],
            "user_id": row[3]
        }
        return user
    else:
        return None

def send_notification(chat_id, message):
    # Отладочный вызов
    logging.debug(f"Sending notification to user with chat_id: {chat_id}")
    logging.debug(f"Message: {message}")

    # Отправка уведомления пользователю через Telegram API
    url = f"https://api.telegram.org/bot{my_bott}/sendMessage"
    data = {"chat_id": chat_id, "text": message}
    response = requests.post(url, json=data)
    if response.status_code != 200:
        logging.error("Failed to send notification: %s", response.text)
        raise ValueError("Failed to send notification")

def ad_user_search(user):
    username = user
    AD_SERVER = var.ldap_srv
    AD_USER = var.ldap_user
    AD_PASSWORD = var.ldap_password
    AD_SEARCH_TREE = var.ldap_ou
    server = Server(AD_SERVER)
    conn = Connection(server,user=AD_USER,password=AD_PASSWORD)
    conn.bind()
    b = '(&(objectCategory=Person)(cn=' + username + '))'
    conn.search(AD_SEARCH_TREE,b, SUBTREE,
        attributes =['cn','proxyAddresses','department','sAMAccountName', 'displayName', 'telephoneNumber', 'ipPhone', 'streetAddress',
        'title','manager','objectGUID','company','lastLogon']
        )
    if len(conn.entries) == 1:
        for entry in conn.entries:
            return str(entry.sAMAccountName)
    else:
        return False

def handle_my_issues_command(bot, message):
    # Получение ID пользователя из базы данных SQLite
    chat_id = message.chat.id
    user_data = get_user_by_id(chat_id)
    if user_data is None:
        bot.reply_to(message, "Вы не зарегистрированы в системе уведомлений.")
        return

    # Получение списка задач, назначенных на текущего пользователя
    current_user = user_data["user_id"]
    issues = jira.search_issues(f"assignee={current_user}")

    if issues:
        # Формирование списка задач в формате "Ключ задачи: Заголовок задачи"
        issue_list = [f"{issue.key}: {issue.fields.summary}" for issue in issues]
        # Возвращение списка задач в виде строки, разделенной переносом строки
        issues_text = '\n'.join(issue_list)
    else:
        issues_text = "У вас нет задач в Jira."

    # Отправка списка задач пользователю
    bot.reply_to(message, issues_text)