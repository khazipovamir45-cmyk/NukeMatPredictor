from flask import Flask, render_template, request, send_file
import sqlite3
import csv
from io import StringIO, BytesIO
import json

from model import load_knn_data, rank_materials, generate_dose_points, generate_temp_points

load_knn_data()

app = Flask(__name__)


def get_corrosion_value(material_name):
    """Возвращает коррозию в мм/год для материала"""
    corrosion_map = {
        "Карбид кремния": "0.002",
        "Сплав ЭК-181": "0.015",
        "Сталь ЭП823-Ш": "0.012",
        "Сталь 316L": "0.035",
        "V-4Cr-4Ti": "0.010",
        "Zircaloy-4": "0.005",
        "Графит": "0.050",
        "UO₂": "0.001",
        "B₄C": "0.008",
        "Инконель 718": "0.003"
    }
    for key, value in corrosion_map.items():
        if key in material_name:
            return value
    return "0.010"


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/form')
def form():
    return render_template('form.html')


@app.route('/result', methods=['POST'])
def result():
    # Получаем данные из формы
    temperature = float(request.form.get('temperature', 850))
    dose = float(request.form.get('dose', 12.5))
    strength = float(request.form.get('strength', 450))
    thermal_cond = float(request.form.get('thermal_cond', 15.5))
    heat_capacity = float(request.form.get('heat_capacity', 500))
    
    # Получаем 3 материала через KNN
    results = rank_materials(temperature, dose, strength, thermal_cond, heat_capacity)
    
    # Форматируем для отображения
    materials_for_template = []
    for material in results:
        corrosion = get_corrosion_value(material.get('name', ''))
        materials_for_template.append({
            'name': material.get('name', 'Неизвестно'),
            'dose': material.get('dose', 0),
            'corrosion': corrosion,
            'status_icon': '★' if material.get('status') == 'optimal' else ('✓' if material.get('status') == 'acceptable' else '✗'),
            'status_class': 'status-best' if material.get('status') == 'optimal' else ('status-good' if material.get('status') == 'acceptable' else 'status-warning'),
            'status_text': material.get('status_text', '')
        })
    
    # Генерируем графики для оптимального материала
    optimal_material = results[0]
    doses, strengths_by_dose = generate_dose_points(optimal_material, T_user=temperature)
    temps, strengths_by_temp = generate_temp_points(optimal_material, dose_user=dose)
    
    return render_template(
        'result.html',
        temperature=temperature,
        dose=dose,
        strength=strength,
        thermal_cond=thermal_cond,
        heat_capacity=heat_capacity,
        materials=materials_for_template,
        optimal_material_name=optimal_material.get('name', 'Оптимальный материал'),
        temp_graph=json.dumps({'x': temps, 'y': strengths_by_temp}),
        dose_graph=json.dumps({'x': doses, 'y': strengths_by_dose})
    )


@app.route('/download_csv')
def download_csv():
    conn = sqlite3.connect('materials.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM materials")
    data = cursor.fetchall()
    columns = [description[0] for description in cursor.description]
    
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(columns)
    writer.writerows(data)
    conn.close()
    
    output.seek(0)
    return send_file(
        BytesIO(output.getvalue().encode('utf-8-sig')),
        as_attachment=True,
        download_name='nukemat_database.csv',
        mimetype='text/csv'
    )


if __name__ == '__main__':
    app.run(debug=True)