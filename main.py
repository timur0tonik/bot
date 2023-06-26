import telebot
from function import ad_user_search, add_user_base, user_fullname_search, chat_id_search,jira_login,create_ticket_jira, my_bot, jira_login, add_comment_to_jira_ticket
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

jira = jira_login()
bot = my_bot

markup = InlineKeyboardMarkup()

button_ticket = InlineKeyboardButton('Создать тикет в HD', callback_data='create_ticket')
button_issues = InlineKeyboardButton('Мои нерешенные тикеты', callback_data='my_issues')

markup.row(button_ticket)
markup.row(button_issues)

@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    try:
        if call.data == 'create_ticket':
            create_task(call.message)
        elif call.data == 'my_issues':
            handle_my_issues_command(bot, call.message)
    except Exception as e:
        print(f"Произошла ошибка: {e}")

def handle_my_issues_command(bot, message):
    try:
        chat_id = message.chat.id
        if not chat_id_search(chat_id):
            my_bot.send_message(chat_id, "Вы не зарегистрированы")
            return
        fullname = user_fullname_search(chat_id)  # получаем объект текущего пользователя
        user = ad_user_search(fullname)  # получаем информацию о пользователе из Active Directory
        issues = jira.search_issues("assignee = {} AND resolution = Unresolved".format(user.email))  # ищем задачи, назначенные на пользователя и не закрытые
        if not issues:
            bot.send_message(chat_id, "У Вас нет нерешенных задач.")
        else:
            for issue in issues:
                bot.send_message(chat_id, f"Задача {issue.key}: {issue.fields.summary}")
    except Exception as e:
        print(f"Произошла ошибка: {e}")

@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    first_name = message.from_user.first_name
    bot.send_message(chat_id, f"Привет, {first_name}! Это бот компании WiseAdvice.\nЯ постараюсь ответить на твои вопросы или помогу создать тикет в Help_Desk.\nЧто тебя интересует?", reply_markup=markup)

# Обработчик команды /my_issues
@bot.message_handler(commands=['my_issues'])
def handle_my_issues(message):
    handle_my_issues_command(bot, message)

# Обработчик команды /add_comment
@bot.message_handler(commands=['add_comment'])
def add_comment(message):
    chat_id = message.chat.id
    if not chat_id_search(chat_id):
        my_bot.send_message(chat_id, "Вы не зарегистрированы")
        return
    bot.send_message(chat_id, "Введите номер задачи:")
    bot.register_next_step_handler(message, add_comment_description)

# Обработчик команды 'Вернуться назад'
@bot.callback_query_handler(func=lambda call: call.data == 'back_to_menu')
def back_to_menu_callback(call):
    chat_id = call.message.chat.id
    first_name = call.from_user.first_name
    bot.send_message(chat_id, f"Привет, {first_name}! Это бот компании WiseAdvice.\nЯ постараюсь ответить на твои вопросы или помогу создать тикет в Help_Desk.\nЧто тебя интересует?", reply_markup=markup)

def add_comment_description(message):
    chat_id = message.chat.id
    if not chat_id_search(chat_id):
        my_bot.send_message(chat_id, "Вы не зарегистрированы")
        return
    issue_key = message.text
    bot.send_message(chat_id, "Введите текст комментария:")
    bot.register_next_step_handler(message, add_comment_text, issue_key)

def add_comment_text(message, issue_key):
    chat_id = message.chat.id
    if not chat_id_search(chat_id):
        my_bot.send_message(chat_id, "Вы не зарегистрированы")
        return
    comment_text = message.text
    if add_comment_to_jira_ticket(issue_key, comment_text):
        my_bot.send_message(chat_id, f"Комментарий '{comment_text}' добавлен в задачу {issue_key}")
    else:
        my_bot.send_message(chat_id, f"Не удалось добавить комментарий в задачу {issue_key}. Попробуйте еще раз.")

def access(message):
    code_access = message.text
    if code_access == 'Доступ02':
        bot.send_message(message.chat.id, f"Введи свое имя: ")
        bot.register_next_step_handler(message, first_names)
    else:
        bot.send_message(message.chat.id, f"Доступ запрещен! Попробуй еще раз!")
        bot.register_next_step_handler(message, access)

def first_names(message):
    global first_name
    first_name = message.text
    bot.send_message(message.chat.id, f"Введи свою фамилию: ")
    bot.register_next_step_handler(message, last_names)

def last_names(message):
    global last_name
    last_name = message.text
    fullname = last_name + ' ' + first_name
    if ad_user_search(fullname) == False:
        bot.send_message(message.chat.id, f'Таких нет в наших местах. \nВведи свое имя: ')
        bot.register_next_step_handler(message, first_names)
    else:
        bot.send_message(message.chat.id, f'Регистрация пройдена!')
        bot.send_message(message.chat.id, f'Если хочешь сообщить о проблеме введи команду /start')
        user = (message.from_user.id, first_name, last_name, ad_user_search(fullname))
        add_user_base(user)
        bot.register_next_step_handler(message, start)

def problem_read(message):
    user = message.from_user.first_name
    text = message.text
    if text == '/create_ticket':
        create_task(message)  # вызываем create_ticket
    elif text == '/add_comment':
        add_comment(message)  # вызываем add_comment


@bot.message_handler(commands=['create_ticket'])
def create_task(message):
    chat_id = message.chat.id
    if not chat_id_search(chat_id):
        my_bot.send_message(chat_id, "Вы не зарегистрированы")
        return
    markup = InlineKeyboardMarkup()
    category_row1 = [InlineKeyboardButton("🌐 VPN", callback_data='category_vpn'),
                     InlineKeyboardButton("📧 Почта", callback_data='category_mail'),
                     InlineKeyboardButton("📞 Телефония", callback_data='category_telephony')]
    category_row2 = [InlineKeyboardButton("🖥 Удаленное подключение", callback_data='category_remote_conn'),
                     InlineKeyboardButton("🤔 Jira", callback_data='category_jira'),
                     InlineKeyboardButton("📖 Confluence", callback_data='category_confluence')]
    category_row3 = [InlineKeyboardButton("⁈ FAQ", callback_data='category_faq'),
                     InlineKeyboardButton("✍ Другое", callback_data='category_other')]
    markup.row(*category_row1)
    markup.row(*category_row2)
    markup.row(*category_row3)
    markup.row(InlineKeyboardButton("Вернуться назад", callback_data='back_to_menu'))
    my_bot.send_message(chat_id, "Предлагаем выбрать одну из категорий", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('category_'))
def handle_category_callback(call):
    category = call.data.split('_')[1]
    chat_id = call.message.chat.id
    if category == 'vpn':
        my_bot.send_message(chat_id, "Введите название задачи:")
        bot.register_next_step_handler(call.message, message, create_task_summary, "")
    elif category == 'mail':
        my_bot.send_message(chat_id, "Введите название задачи:")
        bot.register_next_step_handler(call.message, message, create_task_summary, "")
    elif category == 'telephony':
        my_bot.send_message(chat_id, "Введите название задачи:")
        bot.register_next_step_handler(call.message, message, create_task_summary, "")
    elif category == 'remote_conn':
        my_bot.send_message(chat_id, "Введите название задачи:")
        bot.register_next_step_handler(call.message, message, create_task_summary, "")
    elif category == 'jira':
        my_bot.send_message(chat_id, "Введите название задачи:")
        bot.register_next_step_handler(call.message, message, create_task_summary, "")
    elif category == 'confluence':
        my_bot.send_message(chat_id, "Введите название задачи:")
        bot.register_next_step_handler(call.message, message, create_task_summary, "")
    elif category == 'faq':
        my_bot.send_message(chat_id, "Введите название задачи:")
        bot.register_next_step_handler(call.message, message, create_task_summary, "")
    elif category == 'other':
        my_bot.send_message(chat_id, "Введите название задачи:")
        bot.register_next_step_handler(call.message, message, create_task_summary, "")


@bot.callback_query_handler(func=lambda call: call.data == 'back_to_menu')
def back_to_menu_callback(call):
    chat_id = call.message.chat.id
    my_bot.send_message(chat_id, "Что тебя интересует?", reply_markup=markup)

def create_task_summary(message, description):
    chat_id = message.chat.id
    if not chat_id_search(chat_id):
        my_bot.send_message(chat_id, "Вы не зарегистрированы")
        return
    summary_text = message.text
    bot.send_message(chat_id, "Введите описание задачи:")
    bot.register_next_step_handler(message, create_task_description, summary_text, description)

def create_task_description(message, summary_text, descr_text):
    chat_id = message.chat.id
    if not chat_id_search(chat_id):
        my_bot.send_message(chat_id, "Вы не зарегистрированы")
        return
    descr_text = message.text
    fullname = user_fullname_search(chat_id)  # получаем объект текущего пользователя
    user = ad_user_search(fullname)
    create_ticket_jira(summary_text, fullname, user, descr_text)  # передаем его в функцию create_ticket_jira()
    last_issue = jira.search_issues("project=HD")[0].key
    bot.send_message(chat_id, f"Задача создана! Номер: {last_issue}")

# Обработчик команды /clear
@bot.message_handler(commands=['clear'])
def clear_chat(message):
    chat_id = message.chat.id
    bot.purge_chat(chat_id)

while True:
    try:
        bot.polling(none_stop=True, interval=0)
    except Exception as e:
        print(f"Произошла ошибка: {e}")
        