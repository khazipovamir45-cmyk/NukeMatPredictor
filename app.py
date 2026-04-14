from flask import Flask, render_template, request, redirect, send_file
from model import load_knn_data, rank_materials, generate_dose_points, generate_temp_points

app = Flask(__name__)
load_knn_data()

@app.route('/')
def index():
    """Главная страница (лендинг)"""
    return render_template('index.html')


@app.route('/form')
def form():
    """Страница с формой для ввода параметров"""
    return render_template('form.html')


@app.route('/result', methods=['GET', 'POST'])
def result():
    """
    Обработка формы:
    - GET → редирект на /form
    - POST → обработка данных, вызов модели, показ результатов
    """
    if request.method == 'GET':
        return redirect('/form')

    # Получаем данные из формы
    # app.py (внутри функции result)
    temperature = float(request.form.get('temperature', 0))
    irradiation_dose = float(request.form.get('dose', 0)) # Было 'irradiation_dose'
    min_required_strength = float(request.form.get('strength', 0)) # Было 'min_required_strength'
    heat_capacity = float(request.form.get('heat_capacity', 0))
    thermal_conductivity = float(request.form.get('thermal_cond', 0)) # Было 'thermal_conductivity'
    # Сохраняем параметры для передачи в шаблон
    params = {
        'temperature': temperature,
        'irradiation_dose': irradiation_dose,
        'min_required_strength': min_required_strength,
        'heat_capacity': heat_capacity,
        'thermal_conductivity': thermal_conductivity
    }

    # Ранжируем материалы(пока заглушка)
    ranked_materials = rank_materials(
        temp=temperature,
        dose=irradiation_dose,
        strength=min_required_strength,
        therm_cond=thermal_conductivity,
        heat_cap=heat_capacity
    )

    # Берём лучший материал(первый в списке)
    best_material = ranked_materials[0] if ranked_materials else None

    # Генерируем точки для графиков(пока заглушка)
    # Генерируем точки для графиков
    dose_labels = []
    dose_data = []
    temp_labels = []
    temp_data = []
    
    if best_material:
        # Передаем 'temperature' в качестве T_user
        dose_labels, dose_data = generate_dose_points(best_material, temperature)
        
        # Передаем 'irradiation_dose' в качестве dose_user
        temp_labels, temp_data = generate_temp_points(best_material, irradiation_dose)

    # Передаём всё в result.html
    return render_template(
    'result.html',
    materials=ranked_materials,
    # Передаем параметры напрямую для удобства в HTML
    temperature=temperature,
    dose=irradiation_dose,
    strength=min_required_strength,
    thermal_cond=thermal_conductivity,
    heat_capacity=heat_capacity,
    # Данные для JS графиков (убедитесь, что ключи совпадают с JS)
    temp_graph={'x': temp_labels, 'y': temp_data},
    dose_graph={'x': dose_labels, 'y': dose_data},
    optimal_material_name=best_material['name'] if best_material else "Нет данных"
)


@app.route('/download_xlsx')
def download_xlsx():
    """Скачивание файла materials.xlsx"""
    return send_file('materials.xlsx', as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True)