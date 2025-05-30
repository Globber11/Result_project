import telebot
import json
from core import TaskCore

BOT_TOKEN = "no no no mr. fish"
bot = telebot.TeleBot(BOT_TOKEN)


def load_workers():
    try:
        with open("workers.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def is_authorized(user_id):
    workers = load_workers()
    for worker in workers:
        if "tg_id" in worker and worker["tg_id"] == user_id:
            return True
    return False


def get_worker_by_tg_id(tg_id):
    workers = load_workers()
    for worker in workers:
        if worker.get("tg_id") == tg_id:
            return worker
    return None


def require_auth(func):
    def wrapper(message):
        user_id = message.from_user.id
        if not is_authorized(user_id):
            bot.reply_to(message, "Извините, вы не авторизованы для использования этого бота.")
            return
        return func(message)
    return wrapper


@bot.message_handler(commands=["авторизоваться"])
@require_auth
def send_welcome(message):
    bot.reply_to(message, "Добро пожаловать! Используйте /список_задач для просмотра задач.")


@bot.message_handler(commands=["список_задач"])
@require_auth
def list_tasks(message):
    user_id = message.from_user.id
    worker = get_worker_by_tg_id(user_id)
    if not worker:
        bot.reply_to(message, "Работник не найден.")
        return

    tasks = TaskCore.load_tasks().get(str(worker["id"]), [])
    if not tasks:
        bot.reply_to(message, "У вас нет задач.")
        return

    response = "Ваши задачи:\n"
    total = len(tasks)
    for i, task in enumerate(tasks):
        number = total - i
        # Добавляем глобальный ID в вывод
        response += f"{number}) [ID:{task['global_id']}] {task['title']} (Статус: {task['status']}, до {task['due_date']})\n"

    bot.reply_to(message, response)


@bot.message_handler(commands=["выполнил_задачу"])
@require_auth
def complete_task(message):
    user_id = message.from_user.id
    args = message.text.split()
    if len(args) != 2 or not args[1].isdigit():
        bot.reply_to(message, "Использование: /выполнил_задачу [номер задачи]")
        return

    task_num = int(args[1])
    worker = get_worker_by_tg_id(user_id)
    if not worker:
        bot.reply_to(message, "Работник не найден.")
        return

    tasks_data = TaskCore.load_tasks()
    tasks = tasks_data.get(str(worker["id"]), [])

    if not tasks:
        bot.reply_to(message, "У вас нет задач.")
        return

    if not (1 <= task_num <= len(tasks)):
        bot.reply_to(message, "Некорректный номер задачи.")
        return

    # Помечаем задачу выполненной
    tasks[task_num - 1]["status"] = "Выполнена"
    TaskCore.save_tasks(tasks_data)
    bot.reply_to(message, f"Задача №{task_num} отмечена как выполненная.")


@bot.message_handler(commands=["отклонить_задачу"])
@require_auth
def reject_task(message):
    user_id = message.from_user.id
    args = message.text.split()
    if len(args) != 2 or not args[1].isdigit():
        bot.reply_to(message, "Использование: /отклонить_задачу [номер задачи]")
        return

    task_num = int(args[1])
    worker = get_worker_by_tg_id(user_id)
    if not worker:
        bot.reply_to(message, "Работник не найден.")
        return

    tasks_data = TaskCore.load_tasks()
    tasks = tasks_data.get(str(worker["id"]), [])

    if not tasks:
        bot.reply_to(message, "У вас нет задач.")
        return

    if not (1 <= task_num <= len(tasks)):
        bot.reply_to(message, "Некорректный номер задачи.")
        return

    # Помечаем задачу отклонённой
    tasks[task_num - 1]["status"] = "Отклонена"
    TaskCore.save_tasks(tasks_data)
    bot.reply_to(message, f"Задача №{task_num} отклонена.")



if __name__ == "__main__":
    print("Бот запущен...")
    bot.polling(none_stop=True)
