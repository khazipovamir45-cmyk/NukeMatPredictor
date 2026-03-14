from flask import Flask

# Создаем экземпляр приложения
app = Flask(__name__)

# Определяем простой маршрут
@app.route('/')
def hello():
    return 'Проверяю работу фласка'

# Еще один маршрут для проверки(была пройдена)
# @app.route('/health')
# def health():
#     return 'OK', 200

# Запускаем приложение
if __name__ == '__main__':
    app.run(debug=True)
