import mysql.connector

HOST = "localhost"
USER = "YOUR_USERNAME"
PASSWORD = "YOUR_PASSWORD"
DATABASE = "smart_records"

def get_conn():
    return mysql.connector.connect(
        host=HOST,
        user=USER,
        password=PASSWORD,
        database=DATABASE
    )

def test_db():
    c = get_conn()
    c.close()

# ---------- USERS ----------
def create_user(username, password):
    c = get_conn()
    cur = c.cursor()
    try:
        cur.execute("INSERT INTO users(username, password) VALUES(%s,%s)", (username, password))
        c.commit()
        c.close()
        return True
    except:
        c.close()
        return False

def login_user(username, password):
    c = get_conn()
    cur = c.cursor()
    cur.execute("SELECT id FROM users WHERE username=%s AND password=%s", (username, password))
    row = cur.fetchone()
    c.close()
    if row:
        return row[0]
    return None

# ---------- CUSTOMERS CRUD ----------
def add_customer(user_id, name, phone):
    c = get_conn()
    cur = c.cursor()
    cur.execute("INSERT INTO customers(user_id, name, phone) VALUES(%s,%s,%s)", (user_id, name, phone))
    c.commit()
    c.close()

def get_customers(user_id):
    c = get_conn()
    cur = c.cursor()
    cur.execute("SELECT id, name, phone, created_at FROM customers WHERE user_id=%s ORDER BY id DESC", (user_id,))
    rows = cur.fetchall()
    c.close()
    return rows

def update_customer(customer_id, name, phone):
    c = get_conn()
    cur = c.cursor()
    cur.execute("UPDATE customers SET name=%s, phone=%s WHERE id=%s", (name, phone, customer_id))
    c.commit()
    c.close()

def delete_customer(customer_id):
    c = get_conn()
    cur = c.cursor()
    cur.execute("DELETE FROM customers WHERE id=%s", (customer_id,))
    c.commit()
    c.close()

# ---------- RECORDS CRUD ----------
def add_record(customer_id, title, details):
    c = get_conn()
    cur = c.cursor()
    cur.execute("INSERT INTO records(customer_id, title, details) VALUES(%s,%s,%s)", (customer_id, title, details))
    c.commit()
    c.close()

def get_records(customer_id):
    c = get_conn()
    cur = c.cursor()
    cur.execute("SELECT id, title, details, created_at FROM records WHERE customer_id=%s ORDER BY id DESC", (customer_id,))
    rows = cur.fetchall()
    c.close()
    return rows

def update_record(record_id, title, details):
    c = get_conn()
    cur = c.cursor()
    cur.execute("UPDATE records SET title=%s, details=%s WHERE id=%s", (title, details, record_id))
    c.commit()
    c.close()

def delete_record(record_id):
    c = get_conn()
    cur = c.cursor()
    cur.execute("DELETE FROM records WHERE id=%s", (record_id,))
    c.commit()
    c.close()

def report_summary(user_id):
    c = get_conn()
    cur = c.cursor()

    cur.execute("SELECT COUNT(*) FROM customers WHERE user_id=%s", (user_id,))
    customers_count = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*)
        FROM records r
        JOIN customers cu ON cu.id = r.customer_id
        WHERE cu.user_id=%s
    """, (user_id,))
    records_count = cur.fetchone()[0]

    cur.execute("""
        SELECT cu.name, COUNT(r.id) AS cnt
        FROM customers cu
        LEFT JOIN records r ON r.customer_id = cu.id
        WHERE cu.user_id=%s
        GROUP BY cu.id
        ORDER BY cnt DESC
        LIMIT 5
    """, (user_id,))
    top = cur.fetchall()

    c.close()
    return customers_count, records_count, top
