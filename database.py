import sqlite3
import csv
import os


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
            min_required_strength REAL,
            heat_capacity REAL,
            thermal_conductivity REAL     
        )
    ''')

    conn.commit()
    conn.close()
    print("Таблица 'materials' успешно создана или уже существует")


def load_data_from_csv(csv_file='nuclear_materials.csv'):
    """Загружает данные из CSV файла в БД"""
    if not os.path.exists(csv_file):
        print(f"Файл {csv_file} не найден")
        return

    conn = get_db_connection()
    cursor = conn.cursor()

    with open(csv_file, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        count = 0
        for row in reader:
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO materials 
                    (name, temperature, irradiation_dose, environment_type, min_required_strength, heat_capacity, thermal_conductivity) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    row['name'],
                    float(row['temperature']),
                    float(row['irradiation_dose']),
                    row['environment_type'],
                    float(row['min_required_strength']),
                    float(row['heat_capacity']),
                    float(row['thermal_conductivity'])
                ))
                count += 1
            except Exception as e:
                print(f"Ошибка при вставке {row['name']}: {e}")

    conn.commit()
    conn.close()
    print(f"Загружено {count} материалов в БД")


def get_all_materials():
    """Возвращает все материалы из БД"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM materials ORDER BY name")
    materials = cursor.fetchall()

    conn.close()

    # Преобразование в словари для удобства
    result = []
    for material in materials:
        result.append({
            'id': material['id'],
            'name': material['name'],
            'temperature': material['temperature'],
            'irradiation_dose': material['irradiation_dose'],
            'environment_type': material['environment_type'],
            'min_required_strength': material['min_required_strength'],
            'heat_capacity': material['heat_capacity'],
            'thermal_conductivity': material['thermal_conductivity']
        })

    return result


if __name__ == '__main__':
    init_db()
    load_data_from_csv()
    print("База данных инициализирована")