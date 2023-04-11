from flask import Flask, render_template
import sqlite3
import os

app = Flask(__name__)

DATA_PREFIX = "/home/aaristov/Multicell/"

def readdb(query):
    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()
        cursor.execute(query)
        unique_values = cursor.fetchall()
    return [value[0] for value in unique_values]

@app.route('/')
def index():
    unique_antibiotic_types = readdb('SELECT DISTINCT antibiotic_type FROM datasets;')

    return render_template('index.html', 
                           unique_antibiotic_types=unique_antibiotic_types,
                           )

@app.route('/ab/<antibiotic_type>')
def get_data(antibiotic_type):
    dates = readdb(f"SELECT DISTINCT date FROM datasets WHERE antibiotic_type='{antibiotic_type}';")
    concentrations = [{
        "date": d, 
        "antibiotic_type": antibiotic_type, 
        "concentrations": readdb(
            f"""SELECT  chips.concentration, datasets.path
            FROM datasets 
            JOIN chips 
            ON chips.dataset_id = datasets.id
            WHERE 
            datasets.antibiotic_type='{antibiotic_type}' AND
            datasets.date='{d}'
            ORDER BY chips.concentration;"""),
        "path": os.path.join(DATA_PREFIX, readdb(
            f"""SELECT path
            FROM datasets 
            WHERE
            antibiotic_type='{antibiotic_type}' AND
            date='{d}';""")[0]),
    } for d in dates]
    return concentrations



if __name__ == '__main__':
    app.run(debug=True)
