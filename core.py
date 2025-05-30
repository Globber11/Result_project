import json
import os
from datetime import datetime
from threading import Timer


class TaskCore:
    TASKS_FILE = "tasks.json"
    ID_FILE = "last_task_id.json"
    UPDATE_INTERVAL = 1800  # 30 минут в секундах
    _timer = None

    @classmethod
    def migrate_old_tasks(cls):
        """Добавляет global_id к старым задачам при первом запуске"""
        tasks = cls.load_tasks()
        needs_update = False

        for worker_tasks in tasks.values():
            for task in worker_tasks:
                if "global_id" not in task:
                    task["global_id"] = cls.get_next_task_id()
                    needs_update = True

        if needs_update:
            cls.save_tasks(tasks)

    @classmethod
    def get_next_task_id(cls):
        last_id = 0

        try:
            if os.path.exists(cls.ID_FILE):
                with open(cls.ID_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    last_id = data.get("last_id", 0)
        except (json.JSONDecodeError, OSError) as e:
            raise RuntimeError(f"Ошибка чтения {cls.ID_FILE}: {e}")

        next_id = last_id + 1

        try:
            with open(cls.ID_FILE, "w", encoding="utf-8") as f:
                json.dump({"last_id": next_id}, f)
        except Exception as e:
            raise RuntimeError(f"Ошибка записи {cls.ID_FILE}: {e}")

        return next_id

    @classmethod
    def load_tasks(cls):
        if os.path.exists(cls.TASKS_FILE):
            try:
                with open(cls.TASKS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {}
        return {}

    @classmethod
    def save_tasks(cls, data):
        with open(cls.TASKS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @classmethod
    def delete_worker_tasks(cls, worker_id):
        """Удаляет все задачи работника"""
        tasks = cls.load_tasks()
        worker_key = str(worker_id)
        if worker_key in tasks:
            del tasks[worker_key]
            cls.save_tasks(tasks)

    @classmethod
    def add_task(cls, worker_id, task_data):
        tasks = cls.load_tasks()
        key = str(worker_id)

        # Генерируем ID только для новых задач
        if "global_id" not in task_data:
            task_data["global_id"] = cls.get_next_task_id()

        if key not in tasks:
            tasks[key] = []
        tasks[key].insert(0, task_data)
        cls.save_tasks(tasks)

    @classmethod
    def update_overdue_tasks(cls):
        tasks = cls.load_tasks()
        today = datetime.today()

        for task_list in tasks.values():
            for task in task_list:
                if task["status"] == "в процессе выполнения":
                    try:
                        due_date = datetime.strptime(task["due_date"], "%d.%m.%Y")
                        if today > due_date:
                            task["status"] = "не выполнена"
                    except Exception:
                        continue

        cls.save_tasks(tasks)

    @classmethod
    def start_auto_update(cls):
        cls.update_overdue_tasks()
        cls._timer = Timer(cls.UPDATE_INTERVAL, cls.start_auto_update)
        cls._timer.daemon = True
        cls._timer.start()