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
    Генерация качественного PDF на стороне сервера.
    Использование request.form вместо request.json для совместимости с мобильными браузерами.
    """
    try:
        # Получаем HTML контент. Используем .form, так как это надежнее для скачивания файлов
        html_content = request.form.get('html', '')
        
        if not html_content:
            return 'Нет контента для сохранения', 400
        
        try:
            from weasyprint import HTML, CSS
            
            # Оборачиваем контент в базовую структуру с поддержкой UTF-8
            full_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    @page {{ size: A4; margin: 10mm; }}
                    body {{ font-family: 'Inter', sans-serif; color: #000; background: #fff !important; margin: 0; padding: 0; }}
                    .results-content {{ padding: 20px; }}
                    .results-page {{ background: #fff !important; border: none !important; box-shadow: none !important; }}
                    .table-container {{ border: 1px solid #ccc !important; background: #fff !important; padding: 10px; border-radius: 10px; margin-bottom: 20px; }}
                    .materials-table {{ width: 100%; border-collapse: collapse; }}
                    .materials-table th {{ background: #1e6df2 !important; color: #fff !important; padding: 10px; text-align: left; }}
                    .materials-table td {{ color: #000 !important; border-bottom: 1px solid #eee; padding: 10px; }}
                    .params-badge {{ background: #f0f4f8 !important; color: #000 !important; border: 1px solid #1e6df2 !important; border-radius: 8px; padding: 10px; display: inline-block; margin-bottom: 20px; }}
                    .graph-container {{ border: 1px solid #eee !important; margin-bottom: 20px; break-inside: avoid; padding: 15px; border-radius: 10px; }}
                    .graph-title {{ font-weight: bold; margin-bottom: 10px; color: #1e6df2; }}
                    .graph-frame-wrapper {{ background: #f9f9f9; border: 1px solid #ddd; height: 300px; }}
                    h2 {{ color: #1e6df2; margin-bottom: 20px; }}
                    /* Скрываем кнопки и лишние элементы в PDF */
                    .recalc-section, .custom-header, footer, .recalc-btn, .nav-menu {{ display: none !important; }}
                </style>
            </head>
            <body>
                <div class="results-content">
                    {html_content}
                </div>
            </body>
            </html>
            """
            
            # Генерация PDF в памяти
            pdf_file = HTML(string=full_html).write_pdf()
            
            return send_file(
                BytesIO(pdf_file),
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f'material_report_{os.urandom(3).hex()}.pdf'
            )
            
        except ImportError:
            return 'Ошибка: На сервере не установлен WeasyPrint для генерации PDF', 500
            
    except Exception as e:
        return str(e), 500


@app.route('/download_xlsx')
def download_xlsx():
    """Скачивание файла materials.xlsx"""
    return send_file('materials.xlsx', as_attachment=True)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=False)
