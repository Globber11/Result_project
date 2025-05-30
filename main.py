from core import TaskCore
from manager_interface import MainApp

if __name__ == "__main__":
    TaskCore.start_auto_update()
    app = MainApp()
    app.mainloop()

