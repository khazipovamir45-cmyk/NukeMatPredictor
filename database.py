import sqlite3

DB_PATH = 'materials.db'


def get_db_connection():
    """Создает соединение с базой данных"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Позволяет обращаться по имени колонки
    return conn


def init_db():
    """Создает таблицу materials, если она не существует"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # SQL запрос для создания таблицы
    # (рабочая температура, доза облучения, тип среды, минимальная прочность)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS materials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            temperature REAL,                
            irradiation_dose REAL,         
            environment_type TEXT,         
            min_required_strength REAL     
        )
    ''')

    conn.commit()
    conn.close()
    print("Таблица 'materials' успешно создана или уже существует")


if __name__ == '__main__':
    init_db()
    print("База данных инициализирована")