from flask import Flask, render_template, request, redirect, send_file
from model import load_knn_data, rank_materials, generate_dose_points, generate_temp_points
from functools import lru_cache
import hashlib
import json
from io import BytesIO

app = Flask(__name__)
load_knn_data()

# КЭШ НА 1 МИНУТУ для одинаковых запросов (решает проблему 90%)
@lru_cache(maxsize=256)
def cached_rank_materials(temp, dose, strength, therm_cond, heat_cap):
    """Кэширует результаты расчёта на основе входных параметров"""
    return rank_materials(temp, dose, strength, therm_cond, heat_cap)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/form')
def form():
    return render_template('form.html')

@app.route('/result', methods=['GET', 'POST'])
def result():
    if request.method == 'GET':
        return redirect('/form')

    # Получаем данные
    temperature = float(request.form.get('temperature', 0))
    irradiation_dose = float(request.form.get('dose', 0))
    min_required_strength = float(request.form.get('strength', 0))
    heat_capacity = float(request.form.get('heat_capacity', 0))
    thermal_conductivity = float(request.form.get('thermal_cond', 0))
    
    # ИСПОЛЬЗУЕМ КЭШИРОВАННУЮ ВЕРСИЮ
    ranked_materials = cached_rank_materials(
        temperature, irradiation_dose, min_required_strength,
        thermal_conductivity, heat_capacity
    )
    
    # Берём лучший материал
    best_material = ranked_materials[0] if ranked_materials else None
    
    # Генерация графиков (тоже можно закэшировать, но они зависят от best_material)
    dose_labels, dose_data = [], []
    temp_labels, temp_data = [], []
    
    if best_material:
        dose_labels, dose_data = generate_dose_points(best_material, temperature)
        temp_labels, temp_data = generate_temp_points(best_material, irradiation_dose)
    
    return render_template(
        'result.html',
        materials=ranked_materials,
        temperature=temperature,
        dose=irradiation_dose,
        strength=min_required_strength,
        thermal_cond=thermal_conductivity,
        heat_capacity=heat_capacity,
        temp_graph={'x': temp_labels, 'y': temp_data},
        dose_graph={'x': dose_labels, 'y': dose_data},
        optimal_material_name=best_material['name'] if best_material else "Нет данных"
    )

# ВРЕМЕННО ОТКЛЮЧАЕМ PDF (он жрёт память)
# @app.route('/save-pdf', methods=['POST'])
# def save_pdf():
#     return {'error': 'PDF generation disabled for performance'}, 400

@app.route('/download_xlsx')
def download_xlsx():
    return send_file('materials.xlsx', as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=False)