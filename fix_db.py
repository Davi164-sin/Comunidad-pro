import sqlite3

def add_columns(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    try:
        c.execute("ALTER TABLE usuario ADD COLUMN referral_code VARCHAR(20)")
        print("Added referral_code")
    except sqlite3.OperationalError as e:
        print(f"Error adding referral_code: {e}")
        
    try:
        c.execute("ALTER TABLE usuario ADD COLUMN referred_by INTEGER")
        print("Added referred_by")
    except sqlite3.OperationalError as e:
        print(f"Error adding referred_by: {e}")
        
    conn.commit()
    conn.close()

add_columns("/root/database.db")
