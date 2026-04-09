import sqlite3
import csv
import os

DB_PATH = 'materials.db'

def get_db_connection():
    """Создает соединение с базой данных"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Создает таблицу materials, если она не существует"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS materials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            temperature REAL,
            irradiation_dose REAL,
            min_required_strength REAL,
            heat_capacity REAL,
            thermal_conductivity REAL,
            temp_coef REAL,
            dose_coef REAL,
            corrosion_rate REAL
        )
    ''')
    conn.commit()
    conn.close()
    print("Таблица 'materials' создана")

def load_data_from_csv(csv_file='nuclear_materials.csv'):
    """Загружает данные из CSV файла в БД"""
    if not os.path.exists(csv_file):
        print(f"Файл {csv_file} не найден")
        return

    conn = get_db_connection()
    cursor = conn.cursor()

    with open(csv_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        count = 0
        
        # Проверка: выводим названия колонок
        print("Колонки в CSV:", reader.fieldnames)
        
        for row in reader:
            try:
                # Пробуем вставить
                cursor.execute('''
                    INSERT OR IGNORE INTO materials 
                    (name, temperature, irradiation_dose, min_required_strength, 
                     heat_capacity, thermal_conductivity, temp_coef, dose_coef, corrosion_rate)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    row['name'],
                    float(row['temperature (°C)']),
                    float(row['irradiation_dose (dpa)']),
                    float(row['min_required_strength (MPa)']),
                    float(row['heat_capacity (J/kg·°C)']),
                    float(row['thermal_conductivity (W/m·°C)']),
                    float(row['temp_coef (MPa/°C)']),
                    float(row['dose_coef (MPa/dpa)']),
                    float(row['corrosion_rate (mm/year)'])
                ))
                count += 1
                if count % 20 == 0:
                    print(f"  Загружено {count} материалов...")
                    
            except Exception as e:
                print(f"Ошибка в {row.get('name', '???')}: {e}")
                # Выводим проблемные значения для диагностики
                print(f"  temperature = {row.get('temperature (°C)')}")
                print(f"  irradiation_dose = {row.get('irradiation_dose (dpa)')}")
                print(f"  min_required_strength = {row.get('min_required_strength (MPa)')}")
                print(f"  heat_capacity = {row.get('heat_capacity (J/kg·°C)')}")
                print(f"  thermal_conductivity = {row.get('thermal_conductivity (W/m·°C)')}")
                print(f"  temp_coef = {row.get('temp_coef (MPa/°C)')}")
                print(f"  dose_coef = {row.get('dose_coef (MPa/dpa)')}")
                print(f"  corrosion_rate = {row.get('corrosion_rate (mm/year)')}")
                # Прерываем цикл, чтобы увидеть первую ошибку
                break
    
    conn.commit()
    conn.close()
    print(f"Загружено {count} материалов в БД")

def get_all_materials():
    """Возвращает все материалы из БД"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM materials ORDER BY name")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

if __name__ == '__main__':
    init_db()
    load_data_from_csv()
    
    # Проверяем, что загрузилось
    materials = get_all_materials()
    print(f"Проверка: в БД {len(materials)} материалов")
    if materials:
        print("Первый материал:", materials[0]['name'])
    
    print("База данных инициализирована")