"""
backend.py
==========
This is the "brain" of the application. It contains:
    - Validation rules (donor name required, quantity > 0, etc.)
    - The priority queue logic for Food Requests
    - The FEFO (First Expiry, First Out) distribution logic
    - All database read/write queries used by the GUI

The GUI (gui.py) never talks to SQLite directly - it always calls
a function in this file instead. This keeps the project organized:
if a business rule ever needs to change, there is exactly one
place to change it.

Dates are stored in the database as ISO format "YYYY-MM-DD"
because that format sorts correctly and compares correctly as
plain text. They are only converted to DD/MM/YYYY when displayed
on screen.
"""

import heapq
import re
from collections import deque
from datetime import datetime, timedelta

from database import get_connection

# ============================================================
# CONSTANTS
# ============================================================

PRIORITY_VALUES = {
    "Critical": 1,
    "Emergency": 2,
    "Normal": 3,
}

PRIORITY_NAMES = {v: k for k, v in PRIORITY_VALUES.items()}

DONOR_TYPES = ["Individual", "Restaurant", "Hotel", "Shop", "Organization"]
FOOD_UNITS = ["kg", "litre", "packets", "pieces"]

REQUEST_STATUSES = ["Pending", "Approved", "Completed", "Rejected"]

EXPIRING_SOON_DAYS = 7  # food within this many days of expiry is "Expiring Soon"

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_PATTERN = re.compile(r"^\+?\d[\d\s-]{6,14}\d$")

# In-memory data structures kept for the normal (non-priority) request
# queue, as required by the project. The priority queue used for
# actual processing order is rebuilt from the database, since the
# database is the permanent source of truth (the deque/heap in memory
# would be lost every time the program restarts).
normal_request_queue = deque()
priority_request_heap = []


# ============================================================
# DATE HELPERS
# ============================================================

def today_iso():
    """Returns today's date as 'YYYY-MM-DD', read live from the OS clock."""
    return datetime.now().strftime("%Y-%m-%d")


def iso_to_display(iso_date):
    """Converts 'YYYY-MM-DD' -> 'DD/MM/YYYY' for showing on screen."""
    if not iso_date:
        return ""
    try:
        return datetime.strptime(iso_date, "%Y-%m-%d").strftime("%d/%m/%Y")
    except ValueError:
        return iso_date


def display_to_iso(display_date):
    """Converts 'DD/MM/YYYY' -> 'YYYY-MM-DD' for storing in the database."""
    return datetime.strptime(display_date, "%d/%m/%Y").strftime("%Y-%m-%d")


def format_datetime_display(stored_value):
    """
    Converts a stored 'YYYY-MM-DD HH:MM:SS' timestamp into 'DD/MM/YYYY
    HH:MM' for display, so every date shown in the app - inventory,
    distribution history, everywhere - uses the same DD/MM/YYYY format.
    """
    if not stored_value:
        return ""
    try:
        parsed = datetime.strptime(stored_value, "%Y-%m-%d %H:%M:%S")
        return parsed.strftime("%d/%m/%Y %H:%M")
    except ValueError:
        return stored_value


def compute_expiry_status(iso_expiry_date):
    """
    Returns 'Expired', 'Expiring Soon', or 'Valid' based on today's
    real date compared with the stored expiry date.
    """
    try:
        expiry = datetime.strptime(iso_expiry_date, "%Y-%m-%d").date()
    except ValueError:
        return "Valid"

    today = datetime.now().date()

    if expiry < today:
        return "Expired"
    if expiry <= today + timedelta(days=EXPIRING_SOON_DAYS):
        return "Expiring Soon"
    return "Valid"


# ============================================================
# VALIDATION
# ============================================================

def validate_donor(name, phone, email):
    """Returns an error message string, or None if everything is valid."""
    if not name.strip():
        return "Please enter donor name."
    if phone.strip() and not PHONE_PATTERN.match(phone.strip()):
        return "Please enter a valid phone number."
    if email.strip() and not EMAIL_PATTERN.match(email.strip()):
        return "Please enter a valid email address."
    return None


def validate_quantity(quantity_text):
    """Returns (True, float_value) or (False, error_message)."""
    try:
        value = float(quantity_text)
    except (TypeError, ValueError):
        return False, "Quantity must be a number."
    if value <= 0:
        return False, "Quantity must be greater than 0."
    return True, value


def validate_inventory(food_name, quantity_text, unit, expiry_iso):
    if not food_name.strip():
        return "Please enter food name."
    ok, result = validate_quantity(quantity_text)
    if not ok:
        return result
    if not unit:
        return "Please select a unit."
    if not expiry_iso:
        return "Please select an expiry date."
    if expiry_iso < today_iso():
        return "Expiry date not valid. Expiry date must be today or a future date."
    return None


def validate_request(beneficiary, food_name, quantity_text, priority):
    if not beneficiary.strip():
        return "Please enter beneficiary or NGO name."
    if not food_name.strip():
        return "Please enter the food required."
    ok, result = validate_quantity(quantity_text)
    if not ok:
        return result
    if priority not in PRIORITY_VALUES:
        return "Please select a valid priority."
    return None


# ============================================================
# DONOR MANAGEMENT
# ============================================================

def add_donor(name, phone, email, donor_type):
    error = validate_donor(name, phone, email)
    if error:
        return False, error

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO donors (name, phone, email, donor_type, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (name.strip(), phone.strip(), email.strip(), donor_type,
         datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    )
    conn.commit()
    conn.close()
    return True, "Donor added successfully."


def update_donor(donor_id, name, phone, email, donor_type):
    error = validate_donor(name, phone, email)
    if error:
        return False, error

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE donors
        SET name = ?, phone = ?, email = ?, donor_type = ?
        WHERE id = ?
        """,
        (name.strip(), phone.strip(), email.strip(), donor_type, donor_id),
    )
    conn.commit()
    conn.close()
    return True, "Donor updated successfully."


def delete_donor(donor_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM donors WHERE id = ?", (donor_id,))
    conn.commit()
    conn.close()
    return True, "Donor deleted successfully."


def get_donors(search_text=""):
    conn = get_connection()
    cursor = conn.cursor()
    if search_text.strip():
        pattern = f"%{search_text.strip()}%"
        cursor.execute(
            """
            SELECT id, name, phone, email, donor_type
            FROM donors
            WHERE name LIKE ? OR phone LIKE ? OR email LIKE ?
            ORDER BY id DESC
            """,
            (pattern, pattern, pattern),
        )
    else:
        cursor.execute(
            "SELECT id, name, phone, email, donor_type FROM donors ORDER BY id DESC"
        )
    rows = cursor.fetchall()
    conn.close()
    return rows


# ============================================================
# INVENTORY MANAGEMENT
# ============================================================

def add_inventory_item(food_name, quantity_text, unit, expiry_iso):
    error = validate_inventory(food_name, quantity_text, unit, expiry_iso)
    if error:
        return False, error

    _, quantity = validate_quantity(quantity_text)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO inventory (food_name, quantity, unit, expiry_date, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (food_name.strip(), quantity, unit, expiry_iso,
         datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    )
    conn.commit()
    conn.close()
    return True, "Food item added to inventory."


def get_inventory(search_text=""):
    """
    Returns rows of (id, food_name, quantity, unit, expiry_date_iso, status).
    Existing rows with old/invalid date formats are handled safely -
    their status simply falls back to 'Valid' instead of crashing.
    """
    conn = get_connection()
    cursor = conn.cursor()
    if search_text.strip():
        pattern = f"%{search_text.strip()}%"
        cursor.execute(
            """
            SELECT id, food_name, quantity, unit, expiry_date
            FROM inventory
            WHERE food_name LIKE ?
            ORDER BY expiry_date ASC
            """,
            (pattern,),
        )
    else:
        cursor.execute(
            """
            SELECT id, food_name, quantity, unit, expiry_date
            FROM inventory
            ORDER BY expiry_date ASC
            """
        )
    rows = cursor.fetchall()
    conn.close()

    result = []
    for row_id, food_name, quantity, unit, expiry_date in rows:
        status = compute_expiry_status(expiry_date)
        result.append((row_id, food_name, quantity, unit, expiry_date, status))
    return result


# ============================================================
# FOOD REQUESTS + PRIORITY QUEUE
# ============================================================

def add_request(beneficiary, food_name, quantity_text, priority_text):
    error = validate_request(beneficiary, food_name, quantity_text, priority_text)
    if error:
        return False, error

    _, quantity = validate_quantity(quantity_text)
    priority = PRIORITY_VALUES[priority_text]

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO requests
            (beneficiary, food_name, quantity, priority, status, created_at)
        VALUES (?, ?, ?, ?, 'Pending', ?)
        """,
        (beneficiary.strip(), food_name.strip(), quantity, priority,
         datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    )
    request_id = cursor.lastrowid
    conn.commit()
    conn.close()

    # Push onto the in-memory priority queue too (kept for the data
    # structure requirement). Order key = (priority, request_id) so
    # that same-priority requests are processed oldest-first.
    heapq.heappush(priority_request_heap, (priority, request_id))
    normal_request_queue.append(request_id)

    return True, f"{priority_text} food request submitted successfully."


def get_next_priority_request():
    """
    Pops and returns the request_id that should be handled next,
    according to priority (Critical > Emergency > Normal) and, for
    equal priority, the older request first. Returns None if empty.
    """
    while priority_request_heap:
        priority, request_id = heapq.heappop(priority_request_heap)
        # Skip requests that were already completed/rejected elsewhere.
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM requests WHERE id = ?", (request_id,))
        row = cursor.fetchone()
        conn.close()
        if row and row[0] == "Pending":
            return request_id
    return None


def get_requests(search_text=""):
    conn = get_connection()
    cursor = conn.cursor()
    if search_text.strip():
        pattern = f"%{search_text.strip()}%"
        cursor.execute(
            """
            SELECT id, beneficiary, food_name, quantity, priority, status
            FROM requests
            WHERE beneficiary LIKE ? OR food_name LIKE ?
            ORDER BY priority ASC, id ASC
            """,
            (pattern, pattern),
        )
    else:
        cursor.execute(
            """
            SELECT id, beneficiary, food_name, quantity, priority, status
            FROM requests
            ORDER BY priority ASC, id ASC
            """
        )
    rows = cursor.fetchall()
    conn.close()

    result = []
    for row_id, beneficiary, food_name, quantity, priority, status in rows:
        result.append(
            (row_id, beneficiary, food_name, quantity,
             PRIORITY_NAMES.get(priority, "Normal"), status)
        )
    return result


def update_request_status(request_id, new_status):
    """
    Only allows sensible transitions:
        Pending    -> Approved / Rejected
        Approved   -> Completed / Rejected
    Completed and Rejected are final states.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM requests WHERE id = ?", (request_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return False, "Request not found."

    current_status = row[0]

    allowed = {
        "Pending": {"Approved", "Rejected"},
        "Approved": {"Completed", "Rejected"},
    }

    if new_status not in allowed.get(current_status, set()):
        conn.close()
        return False, f"Cannot change status from {current_status} to {new_status}."

    cursor.execute(
        "UPDATE requests SET status = ? WHERE id = ?", (new_status, request_id)
    )
    conn.commit()
    conn.close()
    return True, f"Request marked as {new_status}."


# ============================================================
# FOOD DISTRIBUTION (FEFO)
# ============================================================

def distribute_food(beneficiary, food_name, quantity_text, request_id=None):
    """
    Distributes food using FEFO (First Expiry, First Out):
        1. Checks the food exists and has enough total stock.
        2. Takes stock from the earliest-expiring batches first.
        3. Updates inventory and records the distribution inside a
           single database transaction, so a failure partway through
           cannot leave the inventory in an inconsistent state.
        4. If a request_id is given, marks that request Completed.

    Returns (success: bool, message: str).
    """
    if not beneficiary.strip():
        return False, "Please select a beneficiary or NGO."
    if not food_name.strip():
        return False, "Please select a food item."

    ok, result = validate_quantity(quantity_text)
    if not ok:
        return False, result
    quantity = result

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("BEGIN")

        cursor.execute(
            """
            SELECT COALESCE(SUM(quantity), 0)
            FROM inventory
            WHERE LOWER(food_name) = LOWER(?) AND quantity > 0
            """,
            (food_name,),
        )
        available = cursor.fetchone()[0]

        if available < quantity:
            conn.rollback()
            conn.close()
            return False, (
                f"Insufficient food available.\n"
                f"Available: {available:g}\n"
                f"Requested: {quantity:g}\n"
                f"Cannot distribute. Available quantity is insufficient."
            )

        # FEFO: earliest expiry_date first, skip expired stock
        today = today_iso()
        cursor.execute(
            """
            SELECT id, quantity
            FROM inventory
            WHERE LOWER(food_name) = LOWER(?)
              AND quantity > 0
              AND expiry_date >= ?
            ORDER BY expiry_date ASC
            """,
            (food_name, today),
        )
        batches = cursor.fetchall()

        remaining = quantity
        for batch_id, batch_quantity in batches:
            if remaining <= 0:
                break
            used = min(batch_quantity, remaining)
            new_quantity = batch_quantity - used
            cursor.execute(
                "UPDATE inventory SET quantity = ? WHERE id = ?",
                (new_quantity, batch_id),
            )
            remaining -= used

        if remaining > 0:
            # Not enough *unexpired* stock even though raw total looked enough
            conn.rollback()
            conn.close()
            return False, (
                "Insufficient food available.\n"
                "Some matching stock has already expired and cannot be used."
            )

        distribution_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            """
            INSERT INTO distributions
                (beneficiary, food_name, quantity, distribution_date, request_id)
            VALUES (?, ?, ?, ?, ?)
            """,
            (beneficiary.strip(), food_name.strip(), quantity,
             distribution_date, request_id),
        )

        if request_id:
            cursor.execute(
                "UPDATE requests SET status = 'Completed' WHERE id = ?",
                (request_id,),
            )

        conn.commit()
        conn.close()
        return True, f"{quantity:g} {food_name} distributed successfully."

    except Exception as exc:  # pragma: no cover - defensive guard
        conn.rollback()
        conn.close()
        return False, f"Distribution failed due to an unexpected error: {exc}"


def get_distributions(search_text=""):
    conn = get_connection()
    cursor = conn.cursor()
    if search_text.strip():
        pattern = f"%{search_text.strip()}%"
        cursor.execute(
            """
            SELECT id, beneficiary, food_name, quantity, distribution_date
            FROM distributions
            WHERE beneficiary LIKE ? OR food_name LIKE ?
            ORDER BY id DESC
            """,
            (pattern, pattern),
        )
    else:
        cursor.execute(
            """
            SELECT id, beneficiary, food_name, quantity, distribution_date
            FROM distributions
            ORDER BY id DESC
            """
        )
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_available_food_names():
    """Distinct food names currently in stock (quantity > 0) - used to
    populate the dropdowns in the Distribution screen."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT DISTINCT food_name FROM inventory
        WHERE quantity > 0
        ORDER BY food_name ASC
        """
    )
    rows = [row[0] for row in cursor.fetchall()]
    conn.close()
    return rows


def get_pending_beneficiaries():
    """Distinct beneficiaries with a Pending or Approved request - used
    to populate the beneficiary dropdown in the Distribution screen."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT DISTINCT beneficiary FROM requests
        WHERE status IN ('Pending', 'Approved')
        ORDER BY beneficiary ASC
        """
    )
    rows = [row[0] for row in cursor.fetchall()]
    conn.close()
    return rows


# ============================================================
# DASHBOARD + REPORTS
# ============================================================

def get_dashboard_stats():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM donors")
    total_donors = cursor.fetchone()[0]

    cursor.execute("SELECT COALESCE(SUM(quantity), 0) FROM inventory WHERE quantity > 0")
    total_food = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM requests WHERE status = 'Pending'")
    pending_requests = cursor.fetchone()[0]

    cursor.execute("SELECT COALESCE(SUM(quantity), 0) FROM distributions")
    total_distributed = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM distributions")
    completed_distributions = cursor.fetchone()[0]

    cursor.execute("SELECT expiry_date FROM inventory WHERE quantity > 0")
    expiry_dates = [row[0] for row in cursor.fetchall()]

    conn.close()

    expiring_soon = sum(
        1 for date in expiry_dates if compute_expiry_status(date) == "Expiring Soon"
    )

    return {
        "total_donors": total_donors,
        "total_food": total_food,
        "pending_requests": pending_requests,
        "total_distributed": total_distributed,
        "expiring_soon": expiring_soon,
        "completed_distributions": completed_distributions,
    }


def get_report_data():
    """
    Returns the data needed for the two Reports page charts:
    Food Status (Available vs Distributed) and Distribution of Foods
    (quantity distributed per food item). All values come straight
    from SQLite - nothing here is sample/fake data.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COALESCE(SUM(quantity), 0) FROM inventory WHERE quantity > 0")
    available = cursor.fetchone()[0]

    cursor.execute("SELECT COALESCE(SUM(quantity), 0) FROM distributions")
    distributed = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT food_name, SUM(quantity) FROM distributions
        GROUP BY food_name ORDER BY SUM(quantity) DESC LIMIT 10
        """
    )
    distribution_by_food = cursor.fetchall()

    conn.close()

    return {
        "food_status": {"Available": available, "Distributed": distributed},
        "distribution_by_food": distribution_by_food,
    }