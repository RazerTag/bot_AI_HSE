import csv
from config import DATABASE_PATH

def save_user_data(name, age):
    with open(DATABASE_PATH, "a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([name, age])

def is_user_registered(user_id):
    with open(DATABASE_PATH, "r") as file:
        reader = csv.reader(file)
        for row in reader:
            if str(user_id) in row:
                return True
    return False

def get_all_users():
    users = []
    with open(DATABASE_PATH, "r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            users.append({"id": row["id"], "name": row["name"], "age": row["age"]})
    return users