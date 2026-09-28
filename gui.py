"""
gui.py
======
Everything the user sees and clicks lives here: the login screen,
the sidebar navigation, the dashboard, and every page (Donors,
Inventory, Food Requests, Food Distribution, Reports).

This file never runs raw SQL. It only calls functions from
backend.py, which is where all validation and business rules live.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date

from tkcalendar import DateEntry
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import backend


# ============================================================
# COLOR PALETTE (soft, food-bank / nature inspired, kept in one place)
# ============================================================

BG_COLOR = "#F7F5EE"          # cream / off-white - main background
WHITE = "#FFFFFF"             # cards
LIGHT_GREEN = "#E9F1E4"       # very light green - info panels, outline buttons
SIDEBAR_COLOR = "#3F6B4A"     # soft/medium green - headings, top bar accents
PRIMARY_COLOR = "#4F7A5B"     # medium green - primary buttons
SECONDARY_COLOR = "#8FBF9F"   # light green - secondary buttons
NEUTRAL_COLOR = "#EDEAE0"     # soft neutral beige/gray - subtle action buttons
NEUTRAL_TEXT = "#3F4A43"
TEXT_COLOR = "#33403A"        # dark gray-green - normal text
TEXT_MUTED = "#6B7770"        # muted gray text
BORDER_COLOR = "#E3E0D4"      # light gray/beige border
DANGER_BG = "#F3E4DE"         # soft, muted red-beige - danger buttons only
DANGER_TEXT = "#9C4A3A"
PLACEHOLDER_COLOR = "#9AA5A0"
TOPBAR_COLOR = "#2F5D42"      # dark green - top title + navigation bar

FONT_APP_TITLE = ("Segoe UI", 15, "bold")
FONT_TITLE = ("Segoe UI", 22, "bold")
FONT_HEADING = ("Segoe UI", 13, "bold")
FONT_LABEL = ("Segoe UI", 10)
FONT_BUTTON = ("Segoe UI", 10, "bold")

CHART_COLORS = ["#4F7A5B", "#8FBF9F", "#C9A66B", "#7A9E7E",
                "#B08968", "#3F6B4A", "#A3B18A", "#6C8A5E",
                "#D9C69C", "#5C7A5F"]


class FoodBankApp:

    def __init__(self, root):
        self.root = root
        self.root.title("Food Bank Management System")
        self.root.geometry("1100x700")
        self.root.minsize(1000, 650)
        self.root.configure(bg=BG_COLOR)

        self.state = {}

        self.show_login()

    # ========================================================
    # WINDOW HELPERS
    # ========================================================

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def clear_content(self):
        for widget in self.content.winfo_children():
            widget.destroy()

    # ========================================================
    # PLACEHOLDER ENTRY HELPER
    # Real example text shown INSIDE the box (e.g. "e.g. Maggie
    # Noodles"). It disappears when the user clicks in and types,
    # and comes back automatically if the box is left empty.
    # ========================================================

    def make_placeholder_entry(self, parent, placeholder, width=20, is_password=False):
        entry = tk.Entry(
            parent, width=width, font=FONT_LABEL, fg=PLACEHOLDER_COLOR,
            relief="solid", bd=1, highlightthickness=0
        )
        entry.insert(0, placeholder)
        entry._placeholder = placeholder
        entry._is_password = is_password

        def on_focus_in(event):
            if entry.get() == entry._placeholder:
                entry.delete(0, tk.END)
                entry.config(fg=TEXT_COLOR)
                if entry._is_password:
                    entry.config(show="*")

        def on_focus_out(event):
            if not entry.get():
                if entry._is_password:
                    entry.config(show="")
                entry.config(fg=PLACEHOLDER_COLOR)
                entry.insert(0, entry._placeholder)

        entry.bind("<FocusIn>", on_focus_in)
        entry.bind("<FocusOut>", on_focus_out)
        return entry

    def get_real_value(self, entry):
        """Returns '' if the entry still shows its placeholder text,
        otherwise returns what the user actually typed."""
        value = entry.get()
        if hasattr(entry, "_placeholder") and value == entry._placeholder:
            return ""
        return value

    def clear_placeholder_entry(self, entry):
        entry.delete(0, tk.END)
        if hasattr(entry, "_placeholder"):
            if getattr(entry, "_is_password", False):
                entry.config(show="")
            entry.config(fg=PLACEHOLDER_COLOR)
            entry.insert(0, entry._placeholder)

    # ========================================================
    # BUTTON STYLE HELPERS
    # (kept distinct so not every button in the app is the same
    # dark green - primary / secondary / outline / danger)
    # ========================================================

    def primary_button(self, parent, text, command):
        return tk.Button(
            parent, text=text, command=command, bg=PRIMARY_COLOR, fg="white",
            activebackground="#255C43", activeforeground="white",
            font=FONT_BUTTON, padx=16, pady=8, relief="flat", cursor="hand2", bd=0
        )

    def secondary_button(self, parent, text, command):
        return tk.Button(
            parent, text=text, command=command, bg=SECONDARY_COLOR, fg="white",
            activebackground="#5FB588", activeforeground="white",
            font=FONT_BUTTON, padx=14, pady=7, relief="flat", cursor="hand2", bd=0
        )

    def outline_button(self, parent, text, command):
        return tk.Button(
            parent, text=text, command=command, bg=LIGHT_GREEN, fg=PRIMARY_COLOR,
            activebackground="#D9EEE1", activeforeground=PRIMARY_COLOR,
            font=FONT_BUTTON, padx=12, pady=6, relief="flat", cursor="hand2", bd=0
        )

    def danger_button(self, parent, text, command):
        return tk.Button(
            parent, text=text, command=command, bg=DANGER_BG, fg=DANGER_TEXT,
            activebackground="#E9D2C9", activeforeground=DANGER_TEXT,
            font=FONT_BUTTON, padx=14, pady=7, relief="flat", cursor="hand2", bd=0
        )

    def subtle_button(self, parent, text, command):
        """A single, consistent, low-key style - used where several
        buttons need to look uniform rather than color-coded."""
        return tk.Button(
            parent, text=text, command=command, bg=NEUTRAL_COLOR, fg=NEUTRAL_TEXT,
            activebackground="#E1DDCF", activeforeground=NEUTRAL_TEXT,
            font=FONT_BUTTON, padx=14, pady=7, relief="flat", cursor="hand2", bd=0
        )

    # ========================================================
    # LOGIN PAGE
    # ========================================================

    def show_login(self):
        self.clear_window()

        outer = tk.Frame(self.root, bg=BG_COLOR)
        outer.pack(fill="both", expand=True)

        card = tk.Frame(outer, bg=WHITE, padx=50, pady=45,
                         highlightbackground=BORDER_COLOR, highlightthickness=1)
        card.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(card, text="Food Bank Management System",
                 font=("Segoe UI", 19, "bold"), fg=SIDEBAR_COLOR, bg=WHITE
                 ).pack(pady=(0, 25))

        tk.Label(card, text="Username", font=FONT_LABEL, bg=WHITE
                 ).pack(anchor="w")
        self.username_entry = self.make_placeholder_entry(card, "e.g. admin", width=32)
        self.username_entry.pack(pady=(4, 14), ipady=5)

        tk.Label(card, text="Password", font=FONT_LABEL, bg=WHITE
                 ).pack(anchor="w")
        self.password_entry = self.make_placeholder_entry(
            card, "Enter password", width=32, is_password=True)
        self.password_entry.pack(pady=(4, 22), ipady=5)

        login_button = self.primary_button(card, "Login", self.login)
        login_button.config(width=27)
        login_button.pack()

        self.username_entry.bind("<Return>", lambda event: self.login())
        self.password_entry.bind("<Return>", lambda event: self.login())
        self.username_entry.focus_set()

    def login(self):
        username = self.get_real_value(self.username_entry).strip()
        password = self.get_real_value(self.password_entry).strip()

        if not username:
            messagebox.showwarning("Login", "Please enter username.")
            return
        if not password:
            messagebox.showwarning("Login", "Please enter password.")
            return
        if username == "admin" and password == "admin":
            self.show_main_application()
        else:
            messagebox.showerror("Login Failed", "Invalid username or password.")

    # ========================================================
    # MAIN APPLICATION SHELL
    # One horizontal top bar: title on the left, navigation menu
    # (horizontal) on the right - no vertical sidebar, so no space
    # is used down the side of the screen.
    # ========================================================

    def show_main_application(self):
        self.clear_window()

        top_bar = tk.Frame(self.root, bg=TOPBAR_COLOR, height=60,
                            highlightbackground=BORDER_COLOR, highlightthickness=1)
        top_bar.pack(side="top", fill="x")
        top_bar.pack_propagate(False)

        tk.Label(top_bar, text="Food Bank Management System",
                 font=FONT_APP_TITLE, bg=TOPBAR_COLOR, fg="white"
                 ).pack(side="left", padx=25)

        nav_area = tk.Frame(top_bar, bg=TOPBAR_COLOR)
        nav_area.pack(side="right", padx=15)

        self.nav_buttons = {}
        nav_items = [
            ("Dashboard", self.show_dashboard),
            ("Donor Management", self.show_donors),
            ("Inventory", self.show_inventory),
            ("Food Requests", self.show_requests),
            ("Food Distribution", self.show_distribution),
            ("Reports", self.show_reports),
        ]
        for label, command in nav_items:
            self.nav_buttons[label] = self.create_nav_button(nav_area, label, command)

        tk.Frame(nav_area, bg="#4A7A5E", width=1
                 ).pack(side="left", fill="y", padx=10, pady=14)

        self.create_nav_button(nav_area, "Logout", self.confirm_logout)

        self.content = tk.Frame(self.root, bg=BG_COLOR)
        self.content.pack(side="top", fill="both", expand=True)

        self.show_dashboard()

    def create_nav_button(self, parent, text, command):
        button = tk.Button(
            parent, text=text, command=command,
            bg=TOPBAR_COLOR, fg="white",
            activebackground="#3F6E52", activeforeground="white",
            font=FONT_BUTTON, padx=12, pady=10,
            relief="flat", bd=0, cursor="hand2"
        )
        button.pack(side="left", padx=2)
        return button

    def set_active_nav(self, active_label):
        for label, button in self.nav_buttons.items():
            button.config(bg="#3F6E52" if label == active_label else TOPBAR_COLOR)

    def confirm_logout(self):
        if messagebox.askyesno("Confirm Logout", "Are you sure you want to logout?"):
            self.show_login()
        # If "No", do nothing - stay on the current page.

    # ========================================================
    # SHARED PAGE HELPERS
    # ========================================================

    def create_header(self, title):
        header = tk.Frame(self.content, bg=BG_COLOR)
        header.pack(fill="x", padx=30, pady=(25, 10))
        tk.Label(header, text=title, font=FONT_TITLE, bg=BG_COLOR,
                 fg=SIDEBAR_COLOR).pack(anchor="w")

    def create_search_bar(self, parent, placeholder, on_search, on_clear):
        """Search + Clear Search only - no Refresh button anywhere."""
        bar = tk.Frame(parent, bg=BG_COLOR)
        bar.pack(fill="x", padx=30, pady=(8, 0))

        search_entry = self.make_placeholder_entry(bar, placeholder, width=42)
        search_entry.pack(side="left", ipady=4)
        search_entry.bind(
            "<Return>", lambda event: on_search(self.get_real_value(search_entry))
        )

        self.outline_button(
            bar, "Search", lambda: on_search(self.get_real_value(search_entry))
        ).pack(side="left", padx=(8, 0))

        def clear_and_reset():
            self.clear_placeholder_entry(search_entry)
            on_clear()

        self.outline_button(bar, "Clear Search", clear_and_reset
                             ).pack(side="left", padx=(8, 0))

        return search_entry

    def create_table(self, parent, columns, headings, widths=None):
        table_frame = tk.Frame(parent, bg=WHITE)
        table_frame.pack(fill="both", expand=True, padx=30, pady=(12, 20))

        scroll_y = ttk.Scrollbar(table_frame, orient="vertical")
        scroll_y.pack(side="right", fill="y")

        table = ttk.Treeview(table_frame, columns=columns, show="headings",
                              yscrollcommand=scroll_y.set)
        scroll_y.config(command=table.yview)

        for col in columns:
            table.heading(col, text=headings[col])
            table.column(col, width=(widths or {}).get(col, 120), anchor="center")

        table.pack(fill="both", expand=True)
        return table

    # ========================================================
    # DASHBOARD
    # ========================================================

    def show_dashboard(self):
        self.clear_content()
        self.set_active_nav("Dashboard")
        self.create_header("Food Bank Operations Dashboard")

        stats = backend.get_dashboard_stats()

        cards_frame = tk.Frame(self.content, bg=BG_COLOR)
        cards_frame.pack(fill="x", padx=30, pady=(5, 10))

        card_data = [
            ("Total Donors", str(stats["total_donors"])),
            ("Total Food Available", f"{stats['total_food']:g} kg"),
            ("Pending Requests", str(stats["pending_requests"])),
            ("Total Food Distributed", f"{stats['total_distributed']:g} kg"),
            ("Expiring Soon", str(stats["expiring_soon"])),
            ("Completed Distributions", str(stats["completed_distributions"])),
        ]

        for index, (title, value) in enumerate(card_data):
            row, col = divmod(index, 3)
            card = tk.Frame(cards_frame, bg=WHITE, padx=18, pady=16,
                             highlightbackground=BORDER_COLOR, highlightthickness=1)
            card.grid(row=row, column=col, sticky="nsew", padx=6, pady=6)
            cards_frame.grid_columnconfigure(col, weight=1)

            tk.Label(card, text=value, font=("Segoe UI", 20, "bold"),
                     bg=WHITE, fg=PRIMARY_COLOR).pack(anchor="w")
            tk.Label(card, text=title, font=("Segoe UI", 10),
                     bg=WHITE, fg=TEXT_MUTED).pack(anchor="w")

        # Plain text "Food Bank Operations" section (no card/button styling)
        panel = tk.Frame(self.content, bg=BG_COLOR)
        panel.pack(fill="both", expand=True, padx=30, pady=(10, 20))

        tk.Label(panel, text="Food Bank Operations", font=FONT_HEADING,
                 bg=BG_COLOR, fg=SIDEBAR_COLOR).pack(anchor="w", pady=(0, 14))

        operations = [
            ("Donor Management", "Manage and track food donors."),
            ("Inventory Management", "Track available food and expiry dates."),
            ("Food Requests", "Manage and prioritize food requests."),
            ("Food Distribution", "Distribute food based on requests and inventory."),
        ]

        for index, (title, description) in enumerate(operations):
            tk.Label(panel, text=title, font=("Segoe UI", 12, "bold"),
                     bg=BG_COLOR, fg=SIDEBAR_COLOR, anchor="w"
                     ).pack(fill="x", pady=(10 if index else 0, 0))
            tk.Label(panel, text=description, font=FONT_LABEL,
                     bg=BG_COLOR, fg=TEXT_MUTED, anchor="w"
                     ).pack(fill="x")

    # ========================================================
    # DONOR MANAGEMENT
    # ========================================================

    def show_donors(self):
        self.clear_content()
        self.set_active_nav("Donor Management")
        self.create_header("Donor Management")

        form = tk.Frame(self.content, bg=WHITE, padx=20, pady=18,
                         highlightbackground=BORDER_COLOR, highlightthickness=1)
        form.pack(fill="x", padx=30)

        self.state["donor_selected_id"] = None

        tk.Label(form, text="Donor Name", bg=WHITE, font=FONT_LABEL).grid(row=0, column=0, sticky="w")
        self.donor_name = self.make_placeholder_entry(form, "e.g. Ramesh Kumar", width=22)
        self.donor_name.grid(row=1, column=0, padx=(0, 15), pady=(2, 8))

        tk.Label(form, text="Phone Number", bg=WHITE, font=FONT_LABEL).grid(row=0, column=1, sticky="w")
        self.donor_phone = self.make_placeholder_entry(form, "e.g. 9876543210", width=16)
        self.donor_phone.grid(row=1, column=1, padx=(0, 15), pady=(2, 8))

        tk.Label(form, text="Email", bg=WHITE, font=FONT_LABEL).grid(row=0, column=2, sticky="w")
        self.donor_email = self.make_placeholder_entry(form, "e.g. name@example.com", width=22)
        self.donor_email.grid(row=1, column=2, padx=(0, 15), pady=(2, 8))

        tk.Label(form, text="Donor Type", bg=WHITE, font=FONT_LABEL).grid(row=0, column=3, sticky="w")
        self.donor_type = ttk.Combobox(form, values=backend.DONOR_TYPES, width=16, state="readonly")
        self.donor_type.grid(row=1, column=3, padx=(0, 15), pady=(2, 8))
        self.donor_type.set(backend.DONOR_TYPES[0])

        button_row = tk.Frame(form, bg=WHITE)
        button_row.grid(row=2, column=0, columnspan=4, sticky="w", pady=(6, 0))

        self.donor_action_button = self.primary_button(button_row, "Add Donor", self.save_donor)
        self.donor_action_button.pack(side="left")

        self.secondary_button(button_row, "Clear Form", self.clear_donor_form
                               ).pack(side="left", padx=(10, 0))

        tk.Label(self.content, text="Registered Donors", font=FONT_HEADING,
                 bg=BG_COLOR, fg=SIDEBAR_COLOR).pack(anchor="w", padx=30, pady=(18, 0))

        self.create_search_bar(
            self.content, "Example: Search donor name, phone or email",
            on_search=lambda text: self.load_donors(text),
            on_clear=lambda: self.load_donors(""),
        )

        columns = ("id", "name", "phone", "email", "type")
        headings = {"id": "ID", "name": "Name", "phone": "Phone",
                    "email": "Email", "type": "Type"}
        widths = {"id": 50, "name": 180, "phone": 120, "email": 200, "type": 120}
        self.donor_table = self.create_table(self.content, columns, headings, widths)

        action_row = tk.Frame(self.content, bg=BG_COLOR)
        action_row.pack(fill="x", padx=30, pady=(0, 20))
        self.secondary_button(action_row, "Edit Selected", self.load_donor_into_form
                               ).pack(side="left")
        self.danger_button(action_row, "Delete Selected", self.remove_selected_donor
                            ).pack(side="left", padx=(10, 0))

        self.load_donors()

    def clear_donor_form(self):
        self.clear_placeholder_entry(self.donor_name)
        self.clear_placeholder_entry(self.donor_phone)
        self.clear_placeholder_entry(self.donor_email)
        self.donor_type.set(backend.DONOR_TYPES[0])
        self.state["donor_selected_id"] = None
        self.donor_action_button.config(text="Add Donor", command=self.save_donor)

    def save_donor(self):
        name = self.get_real_value(self.donor_name)
        phone = self.get_real_value(self.donor_phone)
        email = self.get_real_value(self.donor_email)
        donor_type = self.donor_type.get()

        success, message = backend.add_donor(name, phone, email, donor_type)
        if not success:
            messagebox.showerror("Cannot Add Donor", message)
            return

        messagebox.showinfo("Success", message)
        self.clear_donor_form()
        self.load_donors()

    def load_donor_into_form(self):
        selected = self.donor_table.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a donor to edit.")
            return
        values = self.donor_table.item(selected[0], "values")
        donor_id, name, phone, email, donor_type = values

        for entry, value in ((self.donor_name, name), (self.donor_phone, phone),
                              (self.donor_email, email)):
            entry.delete(0, tk.END)
            entry.config(fg=TEXT_COLOR)
            entry.insert(0, value)
        self.donor_type.set(donor_type)

        self.state["donor_selected_id"] = donor_id
        self.donor_action_button.config(text="Update Donor", command=self.update_selected_donor)

    def update_selected_donor(self):
        donor_id = self.state.get("donor_selected_id")
        if not donor_id:
            return
        success, message = backend.update_donor(
            donor_id, self.get_real_value(self.donor_name),
            self.get_real_value(self.donor_phone),
            self.get_real_value(self.donor_email), self.donor_type.get()
        )
        if not success:
            messagebox.showerror("Cannot Update Donor", message)
            return
        messagebox.showinfo("Success", message)
        self.clear_donor_form()
        self.load_donors()

    def remove_selected_donor(self):
        selected = self.donor_table.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a donor to delete.")
            return
        values = self.donor_table.item(selected[0], "values")
        donor_id, name = values[0], values[1]

        if messagebox.askyesno("Confirm Delete", f"Delete donor '{name}'?"):
            backend.delete_donor(donor_id)
            self.load_donors()

    def load_donors(self, search_text=""):
        for item in self.donor_table.get_children():
            self.donor_table.delete(item)
        for row in backend.get_donors(search_text):
            self.donor_table.insert("", tk.END, values=row)

    # ========================================================
    # INVENTORY
    # ========================================================

    def show_inventory(self):
        self.clear_content()
        self.set_active_nav("Inventory")
        self.create_header("Food Inventory")

        form = tk.Frame(self.content, bg=WHITE, padx=20, pady=18,
                         highlightbackground=BORDER_COLOR, highlightthickness=1)
        form.pack(fill="x", padx=30)

        tk.Label(form, text="Food Name", bg=WHITE, font=FONT_LABEL).grid(row=0, column=0, sticky="w")
        self.food_name = self.make_placeholder_entry(form, "e.g. Maggie Noodles", width=18)
        self.food_name.grid(row=1, column=0, padx=(0, 15), pady=(2, 8))

        tk.Label(form, text="Quantity", bg=WHITE, font=FONT_LABEL).grid(row=0, column=1, sticky="w")
        self.food_quantity = self.make_placeholder_entry(form, "e.g. 2", width=10)
        self.food_quantity.grid(row=1, column=1, padx=(0, 15), pady=(2, 8))

        tk.Label(form, text="Unit", bg=WHITE, font=FONT_LABEL).grid(row=0, column=2, sticky="w")
        self.food_unit = ttk.Combobox(form, values=backend.FOOD_UNITS, width=10, state="readonly")
        self.food_unit.grid(row=1, column=2, padx=(0, 15), pady=(2, 8))
        self.food_unit.set(backend.FOOD_UNITS[0])

        tk.Label(form, text="Expiry Date", bg=WHITE, font=FONT_LABEL).grid(row=0, column=3, sticky="w")
        # tkcalendar's DateEntry gives a proper calendar picker - the user
        # never types a date by hand, and mindate blocks past dates outright.
        self.expiry_picker = DateEntry(
            form, width=16, date_pattern="dd/mm/yyyy", mindate=date.today()
        )
        self.expiry_picker.grid(row=1, column=3, padx=(0, 15), pady=(2, 8))

        self.primary_button(form, "Add Food", self.save_inventory_item
                             ).grid(row=1, column=4, padx=(5, 0))

        tk.Label(self.content, text="Current Inventory", font=FONT_HEADING,
                 bg=BG_COLOR, fg=SIDEBAR_COLOR).pack(anchor="w", padx=30, pady=(18, 0))

        self.create_search_bar(
            self.content, "Example: Search rice, wheat, milk...",
            on_search=lambda text: self.load_inventory(text),
            on_clear=lambda: self.load_inventory(""),
        )

        columns = ("id", "food", "quantity", "unit", "expiry", "status")
        headings = {"id": "ID", "food": "Food Name", "quantity": "Quantity",
                    "unit": "Unit", "expiry": "Expiry Date", "status": "Status"}
        widths = {"id": 50, "food": 180, "quantity": 90, "unit": 90,
                  "expiry": 110, "status": 120}
        self.inventory_table = self.create_table(self.content, columns, headings, widths)

        self.load_inventory()

    def save_inventory_item(self):
        food = self.get_real_value(self.food_name)
        quantity = self.get_real_value(self.food_quantity)
        unit = self.food_unit.get()
        expiry_iso = self.expiry_picker.get_date().strftime("%Y-%m-%d")

        success, message = backend.add_inventory_item(food, quantity, unit, expiry_iso)
        if not success:
            messagebox.showerror("Cannot Add Food", message)
            return

        messagebox.showinfo("Success", message)
        self.clear_placeholder_entry(self.food_name)
        self.clear_placeholder_entry(self.food_quantity)
        self.expiry_picker.set_date(date.today())
        self.load_inventory()

    def load_inventory(self, search_text=""):
        for item in self.inventory_table.get_children():
            self.inventory_table.delete(item)

        for row_id, food, quantity, unit, expiry_iso, status in backend.get_inventory(search_text):
            display_expiry = backend.iso_to_display(expiry_iso)
            tag = status.lower().replace(" ", "_")
            self.inventory_table.insert(
                "", tk.END,
                values=(row_id, food, quantity, unit, display_expiry, status),
                tags=(tag,),
            )
        self.inventory_table.tag_configure("expired", foreground=DANGER_TEXT)
        self.inventory_table.tag_configure("expiring_soon", foreground="#B5651D")
        self.inventory_table.tag_configure("valid", foreground=PRIMARY_COLOR)

    # ========================================================
    # FOOD REQUESTS
    # ========================================================

    def show_requests(self):
        self.clear_content()
        self.set_active_nav("Food Requests")
        self.create_header("Food Requests")

        form = tk.Frame(self.content, bg=WHITE, padx=20, pady=18,
                         highlightbackground=BORDER_COLOR, highlightthickness=1)
        form.pack(fill="x", padx=30)

        tk.Label(form, text="Beneficiary / NGO", bg=WHITE, font=FONT_LABEL).grid(row=0, column=0, sticky="w")
        self.request_beneficiary = self.make_placeholder_entry(form, "e.g. Hope NGO", width=20)
        self.request_beneficiary.grid(row=1, column=0, padx=(0, 15), pady=(2, 8))

        tk.Label(form, text="Food Required", bg=WHITE, font=FONT_LABEL).grid(row=0, column=1, sticky="w")
        self.request_food = self.make_placeholder_entry(form, "e.g. Rice", width=16)
        self.request_food.grid(row=1, column=1, padx=(0, 15), pady=(2, 8))

        tk.Label(form, text="Quantity", bg=WHITE, font=FONT_LABEL).grid(row=0, column=2, sticky="w")
        self.request_quantity = self.make_placeholder_entry(form, "e.g. 5", width=8)
        self.request_quantity.grid(row=1, column=2, padx=(0, 15), pady=(2, 8))

        tk.Label(form, text="Priority", bg=WHITE, font=FONT_LABEL).grid(row=0, column=3, sticky="w")
        self.request_priority = ttk.Combobox(
            form, values=list(backend.PRIORITY_VALUES.keys()), width=14, state="readonly"
        )
        self.request_priority.grid(row=1, column=3, padx=(0, 15), pady=(2, 8))
        self.request_priority.set("Normal")

        button_row = tk.Frame(form, bg=WHITE)
        button_row.grid(row=2, column=0, columnspan=4, sticky="w", pady=(6, 0))

        self.primary_button(button_row, "Submit Request", self.save_request).pack(side="left")
        self.secondary_button(button_row, "Clear Form", self.clear_request_form
                               ).pack(side="left", padx=(10, 0))

        tk.Label(self.content, text="All Requests (ordered by priority)", font=FONT_HEADING,
                 bg=BG_COLOR, fg=SIDEBAR_COLOR).pack(anchor="w", padx=30, pady=(18, 0))

        self.create_search_bar(
            self.content, "Example: Search NGO name or food name",
            on_search=lambda text: self.load_requests(text),
            on_clear=lambda: self.load_requests(""),
        )

        columns = ("id", "beneficiary", "food", "quantity", "priority", "status")
        headings = {"id": "ID", "beneficiary": "Beneficiary / NGO", "food": "Food",
                    "quantity": "Quantity", "priority": "Priority", "status": "Status"}
        widths = {"id": 50, "beneficiary": 170, "food": 140, "quantity": 90,
                  "priority": 100, "status": 100}
        self.request_table = self.create_table(self.content, columns, headings, widths)

        action_row = tk.Frame(self.content, bg=BG_COLOR)
        action_row.pack(fill="x", padx=30, pady=(0, 20))

        self.subtle_button(action_row, "Approve Request",
                            lambda: self.change_request_status("Approved")
                            ).pack(side="left")
        self.subtle_button(action_row, "Reject Request",
                            lambda: self.change_request_status("Rejected")
                            ).pack(side="left", padx=(10, 0))
        self.subtle_button(action_row, "Mark Completed",
                            lambda: self.change_request_status("Completed")
                            ).pack(side="left", padx=(10, 0))

        self.load_requests()

    def clear_request_form(self):
        self.clear_placeholder_entry(self.request_beneficiary)
        self.clear_placeholder_entry(self.request_food)
        self.clear_placeholder_entry(self.request_quantity)
        self.request_priority.set("Normal")

    def save_request(self):
        success, message = backend.add_request(
            self.get_real_value(self.request_beneficiary),
            self.get_real_value(self.request_food),
            self.get_real_value(self.request_quantity),
            self.request_priority.get()
        )
        if not success:
            messagebox.showerror("Cannot Submit Request", message)
            return

        messagebox.showinfo("Success", "Food request submitted successfully.")
        self.clear_request_form()
        self.load_requests()

    def change_request_status(self, new_status):
        selected = self.request_table.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a request first.")
            return
        request_id = self.request_table.item(selected[0], "values")[0]

        success, message = backend.update_request_status(request_id, new_status)
        if not success:
            messagebox.showerror("Cannot Update Request", message)
            return
        messagebox.showinfo("Success", message)
        self.load_requests()

    def load_requests(self, search_text=""):
        for item in self.request_table.get_children():
            self.request_table.delete(item)
        for row in backend.get_requests(search_text):
            self.request_table.insert("", tk.END, values=row)

    # ========================================================
    # FOOD DISTRIBUTION
    # ========================================================

    def show_distribution(self):
        self.clear_content()
        self.set_active_nav("Food Distribution")
        self.create_header("Food Distribution")

        form = tk.Frame(self.content, bg=WHITE, padx=20, pady=18,
                         highlightbackground=BORDER_COLOR, highlightthickness=1)
        form.pack(fill="x", padx=30)

        tk.Label(form, text="Beneficiary / NGO", bg=WHITE, font=FONT_LABEL).grid(row=0, column=0, sticky="w")
        self.distribution_beneficiary = ttk.Combobox(form, width=20)
        self.distribution_beneficiary.grid(row=1, column=0, padx=(0, 15), pady=(2, 8))

        tk.Label(form, text="Food", bg=WHITE, font=FONT_LABEL).grid(row=0, column=1, sticky="w")
        self.distribution_food = ttk.Combobox(form, width=16)
        self.distribution_food.grid(row=1, column=1, padx=(0, 15), pady=(2, 8))

        tk.Label(form, text="Quantity", bg=WHITE, font=FONT_LABEL).grid(row=0, column=2, sticky="w")
        self.distribution_quantity = self.make_placeholder_entry(form, "e.g. 5", width=10)
        self.distribution_quantity.grid(row=1, column=2, padx=(0, 15), pady=(2, 8))

        self.primary_button(form, "Distribute Food", self.perform_distribution
                             ).grid(row=1, column=3, padx=(5, 0))

        self.refresh_distribution_dropdowns()

        tk.Label(self.content, text="Distribution History", font=FONT_HEADING,
                 bg=BG_COLOR, fg=SIDEBAR_COLOR).pack(anchor="w", padx=30, pady=(18, 0))

        self.create_search_bar(
            self.content, "Example: Search beneficiary or food",
            on_search=lambda text: self.load_distributions(text),
            on_clear=lambda: self.load_distributions(""),
        )

        columns = ("id", "beneficiary", "food", "quantity", "date")
        headings = {"id": "ID", "beneficiary": "Beneficiary / NGO", "food": "Food",
                    "quantity": "Quantity", "date": "Date"}
        widths = {"id": 50, "beneficiary": 170, "food": 140, "quantity": 90, "date": 150}
        self.distribution_table = self.create_table(self.content, columns, headings, widths)

        self.load_distributions()

    def refresh_distribution_dropdowns(self):
        self.distribution_beneficiary["values"] = backend.get_pending_beneficiaries()
        self.distribution_food["values"] = backend.get_available_food_names()

    def perform_distribution(self):
        beneficiary = self.distribution_beneficiary.get()
        food = self.distribution_food.get()
        quantity = self.get_real_value(self.distribution_quantity)

        success, message = backend.distribute_food(beneficiary, food, quantity)
        if not success:
            messagebox.showerror("Distribution Failed", message)
            return

        messagebox.showinfo("Success", message)
        self.clear_placeholder_entry(self.distribution_quantity)
        self.refresh_distribution_dropdowns()
        self.load_distributions()

    def load_distributions(self, search_text=""):
        for item in self.distribution_table.get_children():
            self.distribution_table.delete(item)
        for row_id, beneficiary, food, quantity, distribution_date in backend.get_distributions(search_text):
            display_date = backend.format_datetime_display(distribution_date)
            self.distribution_table.insert(
                "", tk.END, values=(row_id, beneficiary, food, quantity, display_date)
            )

    # ========================================================
    # REPORTS
    # ========================================================

    def show_reports(self):
        self.clear_content()
        self.set_active_nav("Reports")
        self.create_header("Reports and Analysis")

        container = tk.Frame(self.content, bg=BG_COLOR)
        container.pack(fill="both", expand=True, padx=30, pady=(10, 20))
        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=1)
        container.grid_rowconfigure(0, weight=1)

        data = backend.get_report_data()

        self.draw_bar_chart(
            container, 0, 0, "Food Status",
            data["food_status"].keys(), data["food_status"].values()
        )

        food_labels = [row[0] for row in data["distribution_by_food"]] or ["No data yet"]
        food_values = [row[1] for row in data["distribution_by_food"]] or [0]
        self.draw_bar_chart(
            container, 0, 1, "Distribution of Foods", food_labels, food_values
        )

    def draw_bar_chart(self, parent, row, col, title, labels, values):
        cell = tk.Frame(parent, bg=WHITE, highlightbackground=BORDER_COLOR,
                         highlightthickness=1)
        cell.grid(row=row, column=col, sticky="nsew", padx=6, pady=6)

        labels = list(labels)
        values = [float(v) for v in values]

        figure = Figure(figsize=(5.6, 4.6), dpi=90)
        axis = figure.add_subplot(111)

        colors = [CHART_COLORS[i % len(CHART_COLORS)] for i in range(len(labels))]
        bars = axis.bar(labels, values, color=colors, edgecolor="white", linewidth=0.5)

        max_value = max(values) if values else 0
        axis.set_ylim(0, max(max_value * 1.25, 1))

        axis.set_title(title, fontsize=12, fontweight="bold", color=TEXT_COLOR)
        axis.grid(axis="y", linestyle="--", alpha=0.4)
        axis.set_axisbelow(True)
        axis.tick_params(axis="x", labelrotation=20, labelsize=9)
        axis.tick_params(axis="y", labelsize=9)
        for spine in ("top", "right"):
            axis.spines[spine].set_visible(False)

        for bar, value in zip(bars, values):
            axis.annotate(f"{value:g}", (bar.get_x() + bar.get_width() / 2, bar.get_height()),
                           textcoords="offset points", xytext=(0, 5),
                           ha="center", fontsize=9, color=SIDEBAR_COLOR)

        figure.tight_layout()

        canvas = FigureCanvasTkAgg(figure, master=cell)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)