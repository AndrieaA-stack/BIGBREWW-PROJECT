import pymysql

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "bigbrew_db",
    "cursorclass": pymysql.cursors.DictCursor,
    "autocommit": True
}

def get_db_connection():
    try:
        return pymysql.connect(**DB_CONFIG)
    except pymysql.Error as e:
        print(f"Database connection error: {e}")
        return None

def fetch_all_menu_items():
    conn = get_db_connection()
    if not conn:
        return []
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, name, price, category FROM menu_items")
            items = cursor.fetchall()
            for item in items:
                item["price"] = float(item["price"])
                item["image"] = None
            return items
    finally:
        conn.close()

def insert_menu_item(name, price, category):
    conn = get_db_connection()
    if not conn:
        return None
    try:
        with conn.cursor() as cursor:
            sql = "INSERT INTO menu_items (name, price, category) VALUES (%s, %s, %s)"
            cursor.execute(sql, (name, price, category))
            return cursor.lastrowid
    finally:
        conn.close()

def update_menu_item_db(item_id, name, price, category):
    conn = get_db_connection()
    if not conn:
        return False
    try:
        with conn.cursor() as cursor:
            sql = "UPDATE menu_items SET name=%s, price=%s, category=%s WHERE id=%s"
            cursor.execute(sql, (name, price, category, item_id))
            return True
    finally:
        conn.close()

def delete_menu_item_db(item_id):
    conn = get_db_connection()
    if not conn:
        return False
    try:
        with conn.cursor() as cursor:
            sql = "DELETE FROM menu_items WHERE id=%s"
            cursor.execute(sql, (item_id,))
            return True
    finally:
        conn.close()

def fetch_all_orders():
    conn = get_db_connection()
    if not conn:
        return []
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT order_id, customer_name, timestamp, total_amount, cash_tendered, change_due "
                "FROM orders ORDER BY order_id DESC"
            )
            return cursor.fetchall()
    finally:
        conn.close()

def insert_order(customer_name, total_amount, cash_tendered, change_due, order_items):
    conn = get_db_connection()
    if not conn:
        return None
    try:
        with conn.cursor() as cursor:
            #TIMESTAMP
            sql_order = """
                INSERT INTO orders (customer_name, timestamp, total_amount, cash_tendered, change_due)
                VALUES (%s, NOW(), %s, %s, %s)
            """
            cursor.execute(sql_order, (customer_name, total_amount, cash_tendered, change_due))
            order_id = cursor.lastrowid

            try:
                for item in order_items:
                    item_details = f"{item['name']} ({item['size']})"
                    if item.get("addons"):
                        item_details += f" + {', '.join(item['addons'])}"
                    sql_items = """
                        INSERT INTO order_items (order_id, item_name, price)
                        VALUES (%s, %s, %s)
                    """
                    cursor.execute(sql_items, (order_id, item_details, item["price"]))
            except Exception:
                pass

            return order_id
    finally:
        conn.close()