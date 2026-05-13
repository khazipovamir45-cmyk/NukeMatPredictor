from flask import Flask, render_template, request, redirect, send_file
from model import load_knn_data, rank_materials, generate_dose_points, generate_temp_points
import os
import json
from io import BytesIO

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
    temperature = float(request.form.get('temperature', 0))
    irradiation_dose = float(request.form.get('dose', 0))
    min_required_strength = float(request.form.get('strength', 0))
    heat_capacity = float(request.form.get('heat_capacity', 0))
    thermal_conductivity = float(request.form.get('thermal_cond', 0))
    
    # Сохраняем параметры для передачи в шаблон
    params = {
        'temperature': temperature,
        'irradiation_dose': irradiation_dose,
        'min_required_strength': min_required_strength,
        'heat_capacity': heat_capacity,
        'thermal_conductivity': thermal_conductivity
    }

    # Ранжируем материалы
    ranked_materials = rank_materials(
        temp=temperature,
        dose=irradiation_dose,
        strength=min_required_strength,
        therm_cond=thermal_conductivity,
        heat_cap=heat_capacity
    )

    # Берём лучший материал (первый в списке)
    best_material = ranked_materials[0] if ranked_materials else None

    # Генерируем точки для графиков
    dose_labels = []
    dose_data = []
    temp_labels = []
    temp_data = []
    
    if best_material:
        dose_labels, dose_data = generate_dose_points(best_material, temperature)
        temp_labels, temp_data = generate_temp_points(best_material, irradiation_dose)

    # Передаём всё в result.html
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


@app.route('/save-pdf', methods=['POST'])
def save_pdf():
    """
    Сохранить PDF отчета (работает везде включая Telegram)
    Используется для Telegram WebApp где window.print() не работает
    """
    try:
        # Получаем HTML контент со страницы
        data = request.json
        html_content = data.get('html', '')
        
        if not html_content:
            return {'error': 'Нет контента для сохранения'}, 400
        
        # Проверяем наличие WeasyPrint
        try:
            from weasyprint import HTML
            
            # Создаём PDF из HTML
            pdf = HTML(string=html_content).write_pdf()
            
            return send_file(
                BytesIO(pdf),
                mimetype='application/pdf',
                as_attachment=True,
                download_name='material_report.pdf'
            )
        except ImportError:
            # Если WeasyPrint не установлен, используем альтернативный метод
            # Возвращаем HTML для обработки на клиенте
            return {
                'error': 'Сервер не настроен для генерации PDF',
                'fallback': True
            }, 400
            
    except Exception as e:
        return {'error': str(e)}, 500


@app.route('/download_xlsx')
def download_xlsx():
    """Скачивание файла materials.xlsx"""
    return send_file('materials.xlsx', as_attachment=True)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=False)
