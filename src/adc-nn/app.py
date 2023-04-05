from flask import Flask, render_template
import sqlite3

app = Flask(__name__)


def get_unique_values(query):
    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()
        cursor.execute(query)
        unique_values = cursor.fetchall()
    return [value[0] for value in unique_values]

@app.route('/')
def index():
    unique_dates = get_unique_values('SELECT DISTINCT date FROM datasets ORDER BY date;')
    unique_antibiotic_types = get_unique_values('SELECT DISTINCT antibiotic_type FROM datasets;')
    unique_concentrations = get_unique_values('SELECT DISTINCT concentration FROM chips;')

    return render_template('index.html', unique_dates=unique_dates,
                           unique_antibiotic_types=unique_antibiotic_types,
                           unique_concentrations=unique_concentrations)


if __name__ == '__main__':
    app.run(debug=True)
