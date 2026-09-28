# Food Distribution Bank Management System

A desktop application for managing food donations, inventory, beneficiary
requests, and food distribution at a food bank.

## Project Description

This system lets a food bank:
- Register donors (people, restaurants, hotels, shops, organizations)
- Track food inventory with expiry dates
- Record and prioritize requests from beneficiaries/NGOs
- Distribute food fairly using **FEFO** (First Expiry, First Out)
- View reports and charts on overall performance

## Features

- Secure login screen
- Dashboard with live statistics
- Donor Management (add, edit, delete, search)
- Inventory with a calendar date picker and automatic expiry status
- Food Requests with a priority queue (Critical / Emergency / Normal)
- Food Distribution using FEFO with transaction-safe database updates
- Reports page with 4 live bar charts (matplotlib)
- Search bar on every page
- Logout confirmation
- Data is saved permanently in SQLite and is never lost between sessions

## Technology Used

| Purpose | Technology |
|---|---|
| Language | Python 3 |
| GUI | Tkinter + ttk |
| Calendar picker | tkcalendar |
| Charts | matplotlib |
| Database | SQLite (built into Python) |
| Data structures | `collections.deque`, `heapq` |

## Project Structure

```
FoodBankProject/
│
├── main.py            # Starting point of the application
├── database.py        # SQLite connection and table creation
├── backend.py         # Validation, priority queue, FEFO logic, report queries
├── gui.py             # All Tkinter screens (login, dashboard, forms, tables, charts)
├── requirements.txt   # Third-party packages needed
├── README.md          # This file
└── food_bank.db        # Created automatically the first time you run the app
```

## How to Install Python

1. Go to https://www.python.org/downloads/
2. Download the latest Python 3 installer for Windows
3. Run it, and **check the box "Add Python to PATH"** before clicking Install

Verify it worked by opening a terminal and typing:
```
python --version
```

## How to Open in VS Code

1. Open VS Code
2. **File → Open Folder** → select the `FoodBankProject` folder
3. Install the **Python** extension (search "Python" by Microsoft in the
   Extensions panel, `Ctrl+Shift+X`) if you don't have it already

## How to Create a Virtual Environment (recommended)

A virtual environment keeps this project's packages separate from the rest
of your computer. In the VS Code terminal (`` Ctrl+` ``):

```
python -m venv venv
```

Activate it (Windows):
```
venv\Scripts\activate
```

You'll know it worked when you see `(venv)` at the start of your terminal line.

## How to Install Dependencies

With the virtual environment activated:
```
pip install -r requirements.txt
```

This installs `tkcalendar` and `matplotlib`. `tkinter`, `sqlite3`, `datetime`,
`heapq`, and `collections` are all already built into Python — nothing to
install for those.

## How to Run

```
python main.py
```

If `python` is not recognized, try:
```
py main.py
```

## Login Credentials

```
Username: admin
Password: admin
```

## How the Modules Work (Simple Explanation)

**Donor Management** — A donor is anyone who gives food to the food bank:
an individual, a restaurant, a hotel, a shop, or an organization. We store
their name, phone, email and type so we know who to thank and who to
contact again.

**Inventory** — Every food item that has been received is stored here with
a quantity, a unit (kg, litre, packets, pieces), and an expiry date.
Expiry validation matters because food banks must never distribute expired
food — the system checks today's real date (from your computer's clock)
every time and blocks any date in the past.

**Food Requests** — A beneficiary or an NGO asks for food. Each request
gets a priority: Critical (highest), Emergency (medium), or Normal
(regular). We use a **priority queue** so that the most urgent requests are
always handled first, even if they were submitted later than a Normal
request.

**Food Distribution** — When food is given out, it becomes a distribution.
The system checks that enough stock exists, then uses FEFO — it always
takes food from the batch with the *earliest* expiry date first, so older
stock never gets forgotten and goes to waste. Inventory is reduced by the
distributed amount, and the record is saved permanently.

### Example, start to finish

```
A restaurant donates 50 kg rice
        ↓
Rice enters Inventory
        ↓
An NGO requests 20 kg rice
        ↓
Request is marked Normal
        ↓
System checks inventory
        ↓
System selects earliest-expiring rice
        ↓
20 kg is distributed
        ↓
Inventory becomes 30 kg
        ↓
Distribution is recorded
        ↓
Report updates
```

## How FEFO Works

FEFO = First Expiry, First Out. If Rice Batch A (10 kg, expires 10/09)
and Rice Batch B (20 kg, expires 20/09) both exist, and someone requests
15 kg, the system takes all 10 kg from Batch A first, then 5 kg from
Batch B — never the other way around. This happens inside a single
database transaction, so if anything goes wrong partway through, nothing
is changed at all (the inventory can never end up half-updated).

## How the Database Works

The first time you run `main.py`, SQLite automatically creates a file
called `food_bank.db` in the project folder — you never create this
file by hand. All your data (donors, inventory, requests, distributions)
is saved permanently inside it. Closing and reopening the app does not
erase anything.

## Testing Checklist

- [ ] Login admin/admin works
- [ ] Wrong username/password rejected
- [ ] Empty login fields show a message
- [ ] Sidebar appears on the right, main content on the left
- [ ] No icons/emojis anywhere
- [ ] Dashboard cards show real numbers
- [ ] Donor add/edit/delete/search works
- [ ] Inventory calendar picker blocks past dates
- [ ] Inventory search works
- [ ] Food Requests priority queue orders Critical > Emergency > Normal
- [ ] Request search and status changes work
- [ ] Food Distribution uses FEFO correctly
- [ ] Insufficient stock shows a clear error
- [ ] Distribution history and search work
- [ ] Reports charts reflect real database data
- [ ] Logout asks for confirmation
- [ ] Data survives closing and reopening the app

## Troubleshooting

**"python is not recognized"** — Reinstall Python and check "Add Python to
PATH", or use `py main.py` instead of `python main.py`.

**`ModuleNotFoundError: No module named 'tkcalendar'` (or `matplotlib`)**
— You haven't installed the dependencies yet. Run:
```
pip install -r requirements.txt
```

**`ModuleNotFoundError: No module named 'tkinter'`** — Very rare on
Windows; it means Python was installed without its standard GUI
component. Reinstall Python from python.org and don't uncheck any
components.

**A traceback (red error text) appears** — Read the *last two lines* of
the error message. It always names the exact file and line number, for
example: `File "gui.py", line 42, in save_donor`. That tells you exactly
where to look.

**The app opens but looks empty/frozen** — Make sure you are running
`main.py`, not `gui.py` or `backend.py` directly.
