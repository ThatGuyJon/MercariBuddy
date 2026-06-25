import os
import sqlite3

try:
    import psycopg2
except ImportError:
    psycopg2 = None


def is_sqlite_conn(connection):
    return sqlite3 is not None and isinstance(connection, sqlite3.Connection)


def create_searches_table(connection, cur):
    if is_sqlite_conn(connection):
        sql = """CREATE TABLE IF NOT EXISTS Searches (
            auto_id INTEGER PRIMARY KEY AUTOINCREMENT,
            discord_id TEXT NOT NULL,
            keyword TEXT NOT NULL,
            last_check BIGINT NOT NULL,
            listings_found INT NOT NULL);"""
    else:
        sql = """CREATE TABLE IF NOT EXISTS Searches (
            auto_id SERIAL PRIMARY KEY,
            discord_id VARCHAR(255) NOT NULL,
            keyword VARCHAR(255) NOT NULL,
            last_check BIGINT NOT NULL,
            listings_found INT NOT NULL);"""

    try:
        cur.execute(sql)
        connection.commit()
        return True
    except Exception as error:
        print("Error creating Searches table:", error)
        return False


def create_stats_table(connection, cur):
    if is_sqlite_conn(connection):
        sql = """CREATE TABLE IF NOT EXISTS Stats (
            auto_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            all_users INT DEFAULT 0,
            all_listings INT DEFAULT 0,
            all_found INT DEFAULT 0);"""
    else:
        sql = """CREATE TABLE IF NOT EXISTS Stats (
            auto_id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL UNIQUE,
            all_users INT DEFAULT 0,
            all_listings INT DEFAULT 0,
            all_found INT DEFAULT 0);"""

    create_default_entry = "INSERT INTO Stats (name) VALUES ('main') ON CONFLICT (name) DO NOTHING;"

    try:
        cur.execute(sql)
        cur.execute(create_default_entry)
        connection.commit()
        return True
    except Exception as error:
        print("Error creating Stats table:", error)
        return False


def database_setup(connection, cur):
    return create_searches_table(connection, cur) and create_stats_table(connection, cur)


def verify_db_connection(connection, cur):
    try:
        if is_sqlite_conn(connection):
            cur.execute("SELECT 1;")
        else:
            cur.execute("SELECT;")
    except Exception as e:
        print("Database connection verify failed:", e)
        return -1

    return 0


def add_to_database(connection, cur, user_id, keyword, unix_time):
    placeholder = '?' if is_sqlite_conn(connection) else '%s'
    # checking if entry already exists
    sql = f"SELECT * FROM Searches WHERE discord_id={placeholder} AND keyword={placeholder};"
    val = (str(user_id), keyword)
    cur.execute(sql, val)
    entries = cur.fetchall()

    # if listing doesnt exist add to database
    if entries == []:
        val = (str(user_id), keyword, unix_time, 0)
        sql = f"""INSERT INTO Searches (discord_id, keyword, last_check, listings_found) VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder})"""
        try:
            cur.execute(sql, val)
            connection.commit()
        except Exception as error:
            print("Error inserting entry:", error)
            return False

        print("Entry inserted successfully into table")
        return True
    else:
        return False


def remove_from_database(connection, cur, user_id, keyword):
    placeholder = '?' if is_sqlite_conn(connection) else '%s'
    sql = f"SELECT * FROM Searches WHERE discord_id={placeholder} AND keyword={placeholder};"
    val = (str(user_id), keyword)
    try:
        cur.execute(sql, val)
        entries = cur.fetchall()
    except Exception as error:
        print("Error checking entry before removal:", error)
        return False

    if entries == []:
        return False
    else:
        sql = f"DELETE FROM Searches WHERE discord_id={placeholder} AND keyword={placeholder};"
        val = (str(user_id), keyword)
        cur.execute(sql, val)
        connection.commit()
        return True


# updates the time for when a listing is found as well as increments a variable containing number of listings found
def update_entry(connection, cur, user_id, keyword, new_time):
    placeholder = '?' if is_sqlite_conn(connection) else '%s'
    sql = f"UPDATE Searches SET last_check={placeholder}, listings_found=listings_found+1 WHERE discord_id={placeholder} AND keyword={placeholder}"
    val = (str(new_time), str(user_id), keyword)
    try:
        cur.execute(sql, val)
        connection.commit()
    except Exception as error:
        print("Error updating entry:", error)


def delete_all_user_entries(connection, cur, user_id):
    placeholder = '?' if is_sqlite_conn(connection) else '%s'
    sql = f"DELETE FROM Searches WHERE discord_id={placeholder};"
    val = (str(user_id),)
    try:
        cur.execute(sql, val)
        connection.commit()
    except Exception as error:
        print("Error deleting user entries:", error)
        return False
    return True


def get_user_entries(connection, cur, user_id):
    placeholder = '?' if is_sqlite_conn(connection) else '%s'
    sql = f"SELECT keyword, listings_found FROM Searches WHERE discord_id={placeholder};"
    val = (str(user_id),)
    try:
        cur.execute(sql, val)
        entries = cur.fetchall()
    except Exception as error:
        print("Error getting user entries:", error)
        return None
    return entries


def get_all_entries(connection, cur):
    sql = "SELECT * FROM Searches;"
    try:
        cur.execute(sql)
        entries = cur.fetchall()
    except Exception as error:
        print("Error getting all entries:", error)
        return None
    return entries


def add_new_user(connection, cur):
    sql = "UPDATE Stats SET all_users=all_users+1 WHERE name='main';"
    try:
        cur.execute(sql)
        connection.commit()
    except Exception as error:
        print("Error updating user stats:", error)
        return False
    return True


def add_listing(connection, cur):
    sql = "UPDATE Stats SET all_listings=all_listings+1 WHERE name='main';"
    try:
        cur.execute(sql)
        connection.commit()
    except Exception as error:
        print("Error updating listing stats:", error)
        return False
    return True


def add_found_listings(connection, cur, num):
    placeholder = '?' if is_sqlite_conn(connection) else '%s'
    sql = f"UPDATE Stats SET all_found=all_found+{placeholder} WHERE name='main';"
    val = (num,)
    try:
        cur.execute(sql, val)
        connection.commit()
    except Exception as error:
        print("Error updating found stats:", error)
        return False
    return True


def get_number_of_unique_users(connection, cur):
    sql = "SELECT COUNT(DISTINCT discord_id) FROM Searches;"
    try:
        cur.execute(sql)
        count = cur.fetchall()
    except Exception as error:
        print("Error getting unique users count:", error)
        return None
    return count


def get_number_of_entries(connection, cur):
    sql = "SELECT COUNT(*) FROM Searches;"
    try:
        cur.execute(sql)
        count = cur.fetchall()
    except Exception as error:
        print("Error getting entries count:", error)
        return None
    return count


def connect_to_database(user, database, password, host, port):
    db_type = os.getenv('DB_TYPE', '').lower()

    # Determine if we should use SQLite
    use_sqlite = (
        db_type == 'sqlite' or
        psycopg2 is None or
        not all([user, database, password, host, port])
    )

    if use_sqlite:
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'mercaribuddy.db')
        print(f"Connecting to SQLite database: {db_path}")
        return sqlite3.connect(db_path)

    try:
        print("Connecting to PostgreSQL database...")
        return psycopg2.connect(
            user=user,
            database=database,
            password=password,
            host=host,
            port=port
        )
    except Exception as error:
        print("Failed to connect to PostgreSQL. Falling back to SQLite...")
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'mercaribuddy.db')
        print(f"Connecting to SQLite database: {db_path}")
        return sqlite3.connect(db_path)
