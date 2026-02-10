import sqlite3

conn = sqlite3.connect('physioclinic.db')
cursor = conn.cursor()

# Get all contact_number values
cursor.execute('SELECT id, name, email, contact_number FROM users')
rows = cursor.fetchall()

print("=== Current Database Contact Data ===\n")
for row in rows:
    user_id, name, email, contact = row
    print(f"ID: {user_id}")
    print(f"Name: {name}")
    print(f"Email: {email}")
    print(f"Contact: {repr(contact)}")
    print(f"Contact Type: {type(contact).__name__}")
    print()

conn.close()
