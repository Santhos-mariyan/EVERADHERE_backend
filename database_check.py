import sqlite3
import json

# Connect to database
conn = sqlite3.connect('physioclinic.db')
cursor = conn.cursor()

# Get contact_number values
cursor.execute('SELECT id, name, email, contact_number FROM users')
rows = cursor.fetchall()

print("\n" + "="*70)
print("DATABASE CONTACT_NUMBER VALUES")
print("="*70 + "\n")

for row in rows:
    user_id, name, email, contact = row
    print(f"User ID: {user_id}")
    print(f"  Name: {name}")
    print(f"  Email: {email}")
    print(f"  Contact Raw: {repr(contact)}")
    print(f"  Contact Type: {type(contact).__name__}")
    if contact:
        print(f"  Contact Length: {len(contact)}")
        print(f"  Contact Characters: {[c for c in contact]}")
    print()

# Check schema
cursor.execute("PRAGMA table_info(users);")
columns = cursor.fetchall()
print("\n" + "="*70)
print("CONTACT_NUMBER COLUMN INFO")
print("="*70 + "\n")
for col in columns:
    if col[1] == 'contact_number':
        print(f"Column Name: {col[1]}")
        print(f"Type: {col[2]}")
        print(f"Not Null: {col[3]}")
        print(f"Default: {col[4]}")

conn.close()
