from flask import Flask, render_template, request, redirect, send_file

app = Flask(__name__)


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
    temperature = float(request.form.get('temperature', 0))
    irradiation_dose = float(request.form.get('irradiation_dose', 0))
    min_required_strength = float(request.form.get('min_required_strength', 0))
    heat_capacity = float(request.form.get('heat_capacity', 0))
    thermal_conductivity = float(request.form.get('thermal_conductivity', 0))

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
        temperature, irradiation_dose, min_required_strength,
        heat_capacity, thermal_conductivity
    )

    # Берём лучший материал(первый в списке)
    best_material = ranked_materials[0] if ranked_materials else None

    # Генерируем точки для графиков(пока заглушка)
    dose_labels = []
    dose_data = []
    temp_labels = []
    temp_data = []
    if best_material:
        dose_labels, dose_data = generate_dose_points(best_material)
        temp_labels, temp_data = generate_temp_points(best_material)

    # Передаём всё в result.html
    return render_template(
        'result.html',
        materials=ranked_materials,
        params=params,
        dose_labels=dose_labels,
        dose_data=dose_data,
        temp_labels=temp_labels,
        temp_data=temp_data
    )


@app.route('/download_xlsx')
def download_xlsx():
    """Скачивание файла materials.xlsx"""
    return send_file('materials.xlsx', as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True)