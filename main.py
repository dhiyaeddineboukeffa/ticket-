import tkinter as tk
from app import PeopleCounterApp 

if __name__ == "__main__":
    root = tk.Tk()
    app = PeopleCounterApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
