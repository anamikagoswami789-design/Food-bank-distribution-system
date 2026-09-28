"""
main.py
=======
This is the file you run. It does exactly two things:
    1. Makes sure the database and its tables exist.
    2. Opens the application window.

Run it with:
    python main.py
"""

import tkinter as tk

from database import initialize_database
from gui import FoodBankApp

if __name__ == "__main__":
    initialize_database()

    root = tk.Tk()
    app = FoodBankApp(root)
    root.mainloop()
