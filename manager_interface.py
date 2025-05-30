from core import TaskCore
import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import json


class Worker:
    def __init__(self, worker_id, name, tg_id=None):
        self.worker_id = worker_id
        self.name = name
        self.tg_id = tg_id


class TaskAssignmentWindow(tk.Toplevel):
    def __init__(self, master, worker: Worker):
        super().__init__(master)
        self.title(f"Выдать задачу: {worker.name}")
        self.geometry("400x300")
        self.worker = worker

        tk.Label(self, text="Название задачи:").pack(anchor='w', padx=10, pady=(10, 0))
        self.title_entry = tk.Entry(self)
        self.title_entry.pack(fill='x', padx=10)

        tk.Label(self, text="Описание задачи:").pack(anchor='w', padx=10, pady=(10, 0))
        self.description_text = tk.Text(self, height=5)
        self.description_text.pack(fill='both', padx=10, pady=5)

        tk.Label(self, text="Дата завершения (ДД.ММ.ГГГГ):").pack(anchor='w', padx=10, pady=(10, 0))
        self.due_date_entry = tk.Entry(self)
        self.due_date_entry.pack(fill='x', padx=10)

        button_frame = tk.Frame(self)
        button_frame.pack(pady=15)
        tk.Button(button_frame, text="Выдать", command=self.assign_task).pack(side='left', padx=5)
        tk.Button(button_frame, text="Отмена", command=self.destroy).pack(side='left', padx=5)

    def assign_task(self):
        title = self.title_entry.get().strip()
        description = self.description_text.get("1.0", tk.END).strip()
        due_date = self.due_date_entry.get().strip()

        if not title or not description or not due_date:
            messagebox.showerror("Ошибка", "Пожалуйста, заполните все поля.")
            return

        try:
            datetime.strptime(due_date, "%d.%m.%Y")
        except ValueError:
            messagebox.showerror("Ошибка", "Неверный формат даты.")
            return

        task_data = {
            "title": title,
            "description": description,
            "due_date": due_date,
            "status": "в процессе выполнения"
        }

        try:
            TaskCore.add_task(self.worker.worker_id, task_data)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить задачу: {e}")
            return

        messagebox.showinfo("Успех", f"Задача выдана сотруднику {self.worker.name}.")
        self.destroy()



class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Менеджер задач")
        self.geometry("550x500")
        self.workers = self.load_workers()
        self.create_widgets()

    def generate_report(self):
        import pandas as pd
        from tkinter import filedialog, messagebox  # убедитесь, что messagebox импортирован

        try:
            task_data = TaskCore.load_tasks()
            rows = []

            for worker in self.workers:
                w_id = str(worker.worker_id)
                w_name = worker.name
                w_tg_id = worker.tg_id

                tasks = task_data.get(w_id, [])
                for idx, task in enumerate(tasks, start=1):
                    rows.append({
                        "Локальный ID": idx,
                        "Глобальный ID": task.get("global_id"),  # Добавлен глобальный ID
                        "Работник": w_name,
                        "Telegram ID": w_tg_id,
                        "Название задачи": task.get("title"),
                        "Описание": task.get("description"),
                        "Статус": task.get("status"),
                        "Срок выполнения": task.get("due_date"),
                    })

            if not rows:
                messagebox.showinfo("Информация", "Нет задач для формирования отчёта.")
                return

            df = pd.DataFrame(rows)
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel файлы", "*.xlsx")],
                title="Сохранить отчёт как..."
            )
            if file_path:
                df.to_excel(file_path, index=False)
                messagebox.showinfo("Готово", f"Отчёт успешно сохранён:\n{file_path}")

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось создать отчёт:\n{e}")

    def load_workers(self):
        try:
            with open("workers.json", "r", encoding="utf-8") as file:
                data = json.load(file)
                return [Worker(worker["id"], worker["name"], worker.get("tg_id")) for worker in data]
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка загрузки workers.json: {e}")
            return []

    def save_workers(self):
        try:
            data = [{"id": w.worker_id, "name": w.name, "tg_id": w.tg_id} for w in self.workers]
            with open("workers.json", "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка сохранения workers.json: {e}")

    def create_widgets(self):
        tk.Label(self, text="Список работников:", font=("Arial", 14)).pack(pady=10)

        add_btn = tk.Button(self, text="Добавить работника", command=self.add_worker_window)
        add_btn.pack(pady=(0, 10))
        report_btn = tk.Button(self, text="Сформировать отчёт", command=self.generate_report)
        report_btn.pack(pady=(0, 10))

        self.container = tk.Frame(self)
        self.container.pack(fill='both', expand=True)

        self.render_worker_list()

    def render_worker_list(self):
        for widget in self.container.winfo_children():
            widget.destroy()

        for worker in self.workers:
            frame = tk.Frame(self.container)
            frame.pack(fill='x', pady=5, padx=10)

            display_text = f"{worker.name} (tg_id: {worker.tg_id if worker.tg_id else 'не задан'})"
            tk.Label(frame, text=display_text, width=30, anchor='w').pack(side='left')

            tk.Button(frame, text="Список задач", command=lambda w=worker: self.open_task_list(w)).pack(side='left', padx=5)
            tk.Button(frame, text="Выдать задачу", command=lambda w=worker: self.open_task_window(w)).pack(side='left', padx=5)
            tk.Button(frame, text="Редактировать", command=lambda w=worker: self.edit_worker_window(w)).pack(side='left', padx=5)

    def edit_worker_window(self, worker):
        window = tk.Toplevel(self)
        window.title(f"Редактировать работника: {worker.name}")
        window.geometry("320x220")

        tk.Label(window, text="Имя:").pack(anchor='w', padx=10, pady=(10, 0))
        name_entry = tk.Entry(window)
        name_entry.insert(0, worker.name)
        name_entry.pack(fill='x', padx=10)

        tk.Label(window, text="Telegram ID:").pack(anchor='w', padx=10, pady=(10, 0))
        tg_id_entry = tk.Entry(window)
        tg_id_entry.insert(0, str(worker.tg_id) if worker.tg_id else "")
        tg_id_entry.pack(fill='x', padx=10)

        def save_changes():
            new_name = name_entry.get().strip()
            new_tg_id_text = tg_id_entry.get().strip()

            if not new_name or not new_tg_id_text:
                messagebox.showerror("Ошибка", "Пожалуйста, заполните все поля.")
                return

            if not new_tg_id_text.isdigit():
                messagebox.showerror("Ошибка", "Telegram ID должен быть числом.")
                return

            new_tg_id = int(new_tg_id_text)
            if new_tg_id != worker.tg_id and any(w.tg_id == new_tg_id for w in self.workers):
                messagebox.showerror("Ошибка", "Работник с таким Telegram ID уже существует.")
                return

            worker.name = new_name
            worker.tg_id = new_tg_id

            self.save_workers()
            self.render_worker_list()
            window.destroy()

        def delete_worker():
            if messagebox.askyesno("Подтверждение", f"Удалить работника {worker.name}?"):
                if messagebox.askyesno("Внимание!",
                                       "Вы уверены, что хотите удалить этого работника? Это действие необратимо."):
                    try:
                        # Загрузка всех задач
                        all_tasks = TaskCore.load_tasks()

                        # Ключ для поиска задач работника
                        worker_key = str(worker.worker_id)

                        # Удаление ВСЕХ задач работника
                        if worker_key in all_tasks:
                            del all_tasks[worker_key]
                            TaskCore.save_tasks(all_tasks)

                        # Удаление работника из списка
                        self.workers = [w for w in self.workers if w.worker_id != worker.worker_id]
                        self.save_workers()
                        self.render_worker_list()
                        window.destroy()

                    except Exception as e:
                        messagebox.showerror("Ошибка", f"Ошибка при удалении работника: {e}")

        btn_frame = tk.Frame(window)
        btn_frame.pack(pady=15)
        tk.Button(btn_frame, text="Сохранить", command=save_changes).pack(side='left', padx=5)
        tk.Button(btn_frame, text="Отмена", command=window.destroy).pack(side='left', padx=5)

        del_btn = tk.Button(window, text="Удалить работника", fg="white", bg="red", command=delete_worker)
        del_btn.pack(pady=10, fill='x', padx=10)

    def add_worker_window(self):
        window = tk.Toplevel(self)
        window.title("Добавить работника")
        window.geometry("300x180")

        tk.Label(window, text="Имя:").pack(anchor='w', padx=10, pady=(10, 0))
        name_entry = tk.Entry(window)
        name_entry.pack(fill='x', padx=10)

        tk.Label(window, text="Telegram ID:").pack(anchor='w', padx=10, pady=(10, 0))
        tg_id_entry = tk.Entry(window)
        tg_id_entry.pack(fill='x', padx=10)

        def add_worker():
            name = name_entry.get().strip()
            tg_id_text = tg_id_entry.get().strip()

            if not name or not tg_id_text:
                messagebox.showerror("Ошибка", "Пожалуйста, заполните все поля.")
                return

            if not tg_id_text.isdigit():
                messagebox.showerror("Ошибка", "Telegram ID должен быть числом.")
                return

            tg_id = int(tg_id_text)
            new_id = max((w.worker_id for w in self.workers), default=0) + 1

            # Проверка на уникальность tg_id
            if any(w.tg_id == tg_id for w in self.workers):
                messagebox.showerror("Ошибка", "Работник с таким Telegram ID уже существует.")
                return

            new_worker = Worker(new_id, name, tg_id)
            self.workers.append(new_worker)
            self.save_workers()
            self.render_worker_list()
            window.destroy()

        btn_frame = tk.Frame(window)
        btn_frame.pack(pady=15)
        tk.Button(btn_frame, text="Добавить", command=add_worker).pack(side='left', padx=5)
        tk.Button(btn_frame, text="Отмена", command=window.destroy).pack(side='left', padx=5)

    def open_task_window(self, worker):
        TaskAssignmentWindow(self, worker)

    def open_task_list(self, worker):
        TaskListWindow(self, worker)

class TaskListWindow(tk.Toplevel):
    def __init__(self, master, worker):
        super().__init__(master)
        self.worker = worker
        self.title(f"Список задач {worker.name}")
        self.geometry("400x400")

        self.tasks = TaskCore.load_tasks().get(str(worker.worker_id), [])
        self.create_widgets()

    def create_widgets(self):
        for task in self.tasks:
            frame = tk.Frame(self, pady=5)
            frame.pack(fill='x', padx=10)

            # Добавляем отображение глобального ID
            display_text = f"[Глобальный ID: {task['global_id']}] {task['title']}"
            tk.Label(frame, text=display_text, anchor='w').pack(side='left', expand=True, fill='x')
            tk.Button(frame, text="Развернуть", command=lambda t=task: self.show_details(t)).pack(side='right')

    def show_details(self, task):
        detail_win = tk.Toplevel(self)
        detail_win.title("Детали задачи")
        detail_win.geometry("350x250")

        tk.Label(detail_win, text=f"Название: {task['title']}", anchor='w').pack(fill='x', padx=10, pady=5)
        tk.Label(detail_win, text=f"Глобальный ID: {task['global_id']}", anchor='w').pack(fill='x', padx=10, pady=5)
        tk.Label(detail_win, text=f"Описание: {task['description']}", anchor='w', wraplength=300, justify='left').pack(fill='x', padx=10, pady=5)
        tk.Label(detail_win, text=f"Срок: {task['due_date']}", anchor='w').pack(fill='x', padx=10, pady=5)
        tk.Label(detail_win, text=f"Статус: {task['status']}", anchor='w').pack(fill='x', padx=10, pady=5)
