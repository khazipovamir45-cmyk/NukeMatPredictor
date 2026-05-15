from flask import Flask, render_template, request, redirect, send_file
from model import load_knn_data, compute_full_result
from functools import lru_cache
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
load_knn_data()


def safe_float(value, default=0.0):
    """Безопасное приведение к float — не падает на пустых полях и мусоре в форме."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


@lru_cache(maxsize=256)
def _cached_full_result(temp, dose, strength, therm_cond, heat_cap):
    """Кэш считает материалы и оба графика разом — один проход на повторный запрос."""
    return compute_full_result(temp, dose, strength, therm_cond, heat_cap)


def cached_full_result(temp, dose, strength, therm_cond, heat_cap):
    """Округление параметров перед обращением к кэшу — повышает hit rate."""
    return _cached_full_result(
        round(temp, 1),
        round(dose, 2),
        round(strength, 1),
        round(therm_cond, 2),
        round(heat_cap, 1),
    )


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/form')
def form():
    return render_template('form.html')


@app.route('/health')
def health():
    """Лёгкий эндпоинт для крон-пинга — не рендерит шаблоны, экономит CPU."""
    return 'ok', 200


@app.route('/result', methods=['GET', 'POST'])
def result():
    if request.method == 'GET':
        return redirect('/form')

    temperature = safe_float(request.form.get('temperature'))
    irradiation_dose = safe_float(request.form.get('dose'))
    min_required_strength = safe_float(request.form.get('strength'))
    heat_capacity = safe_float(request.form.get('heat_capacity'))
    thermal_conductivity = safe_float(request.form.get('thermal_cond'))

    ranked_materials, dose_points, temp_points = cached_full_result(
        temperature, irradiation_dose, min_required_strength,
        thermal_conductivity, heat_capacity
    )

    best_material = ranked_materials[0] if ranked_materials else None

    return render_template(
        'result.html',
        materials=ranked_materials,
        temperature=temperature,
        dose=irradiation_dose,
        strength=min_required_strength,
        thermal_cond=thermal_conductivity,
        heat_capacity=heat_capacity,
        temp_graph={'x': temp_points[0], 'y': temp_points[1]},
        dose_graph={'x': dose_points[0], 'y': dose_points[1]},
        optimal_material_name=best_material['name'] if best_material else "Нет данных"
    )


@app.route('/download_xlsx')
def download_xlsx():
    return send_file(os.path.join(BASE_DIR, 'materials.xlsx'), as_attachment=True)


if __name__ == '__main__':
    # Здесь будем делать запуск через gunicorn
    app.run(host='0.0.0.0', port=10000, debug=False)
