from flask import Flask, render_template

app = Flask(__name__)

# Маршрут для главной страницы (лендинг)
@app.route('/')
def index():
    return render_template('index.html')

# Маршрут для страницы с формой
@app.route('/form')
def form():
    return render_template('form.html')

if __name__ == '__main__':
    app.run(debug=True)

