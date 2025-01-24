import csv
import os
from datetime import datetime

USERS_CSV = "users.csv"
EVENTS_CSV = "events.csv"
ATTEND_CSV = "attend.csv"

def ensure_csv_headers(filename, fieldnames):
    """Создаёт CSV-файл с заголовками, если он отсутствует."""
    if not os.path.exists(filename):
        with open(filename, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

def init_csv_files():
    ensure_csv_headers(USERS_CSV, ["user_id", "first_name", "last_name", "total_points"])
    ensure_csv_headers(EVENTS_CSV, ["event_id", "name", "date", "place", "points"])
    ensure_csv_headers(ATTEND_CSV, ["user_id", "event_id", "checkin_time", "points_earned"])

def load_users():
    data = {}
    with open(USERS_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            data[row["user_id"]] = {
                "first_name": row["first_name"],
                "last_name": row["last_name"],
                "total_points": int(row["total_points"])
            }
    return data

def save_user(user_id, first_name, last_name):
    users = load_users()
    users[str(user_id)] = {
        "first_name": first_name,
        "last_name": last_name,
        "total_points": 0
    }
    _write_users(users)

def _write_users(users_dict):
    with open(USERS_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["user_id","first_name","last_name","total_points"])
        writer.writeheader()
        for uid, info in users_dict.items():
            writer.writerow({
                "user_id": uid,
                "first_name": info["first_name"],
                "last_name": info["last_name"],
                "total_points": info["total_points"]
            })

def is_registered(user_id):
    return str(user_id) in load_users()

def update_user_points(user_id, delta_points):
    users = load_users()
    uid = str(user_id)
    if uid in users:
        users[uid]["total_points"] += delta_points
        _write_users(users)

def load_events():
    ensure_csv_headers(EVENTS_CSV, ["event_id","name","date","place","points","description"])

def save_event(event_id, name, date_str, place, points, description=""):
    events = load_events()
    events[event_id] = {
        "name": name,
        "date": date_str,
        "place": place,
        "points": points,
        "description": description
    }
    with open(EVENTS_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["event_id","name","date","place","points","description"])
        writer.writeheader()
        for eid, info in events.items():
            writer.writerow({
                "event_id": eid,
                "name": info["name"],
                "date": info["date"],
                "place": info["place"],
                "points": info["points"],
                "description": info.get("description","")
            })

def load_attendance():
    entries = []
    with open(ATTEND_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["points_earned"] = int(row["points_earned"])
            entries.append(row)
    return entries

def save_attendance(user_id, event_id, points):
    with open(ATTEND_CSV, "a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["user_id","event_id","checkin_time","points_earned"])
        if os.path.getsize(ATTEND_CSV) == 0:
            writer.writeheader()
        writer.writerow({
            "user_id": user_id,
            "event_id": event_id,
            "checkin_time": datetime.now().isoformat(),
            "points_earned": points
        })