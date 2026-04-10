from flask import Flask, render_template, request, send_file
import sqlite3
import csv
from io import StringIO, BytesIO

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/form')
def form():
    return render_template('form.html')

@app.route('/result', methods=['POST'])
def result():
    # Код из репозитория (оставьте как есть или добавьте свой)
    # Это заглушка - замените на реальный код из репозитория
    return render_template('result.html')

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