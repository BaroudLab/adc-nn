from flask import Flask, render_template
import sqlite3
import os
import logging
import dask.array as da
from .io import encode_base64

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

app = Flask(__name__)

DATA_PREFIX = "/home/aaristov/Multicell/"

def readdb(query, unique=True):
    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()
        cursor.execute(query)
        values = cursor.fetchall()
    if unique:
        return [v[0] for v in values]
    return values

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
            f"""SELECT  chips.concentration, datasets.unit, datasets.path
            FROM datasets 
            JOIN chips 
            ON chips.dataset_id = datasets.id
            WHERE 
            datasets.antibiotic_type='{antibiotic_type}' AND
            datasets.date='{d}'
            ORDER BY chips.concentration;"""),
        "paths": readdb(
            f"""SELECT  datasets.path
            FROM datasets 
            JOIN chips 
            ON chips.dataset_id = datasets.id
            WHERE 
            datasets.antibiotic_type='{antibiotic_type}' AND
            datasets.date='{d}'
            ORDER BY chips.concentration;"""),
        
        "chip_id": readdb(
            f"""SELECT  chips.chip_id
            FROM datasets 
            JOIN chips 
            ON chips.dataset_id = datasets.id
            WHERE 
            datasets.antibiotic_type='{antibiotic_type}' AND
            datasets.date='{d}'
            ORDER BY chips.concentration;"""),
        
    } for d in dates]
    return concentrations

@app.route("/ab/<ab>/<date>/<concentration>/<index>")
def get_images(ab,date, concentration, index):
    path, chip_id = readdb(
            f"""SELECT  datasets.path, chips.chip_id
            FROM datasets 
            JOIN chips 
            ON chips.dataset_id = datasets.id
            WHERE 
            datasets.antibiotic_type='{ab}' AND
            datasets.date='{date}' AND
            chips.concentration={concentration}
            ;""", unique=False)[0]
    logger.debug(f"retrieved path: {path}, chip_id: {chip_id}")

    abs_path = os.path.join(DATA_PREFIX, path)
    logger.debug(f"abs_path {abs_path}")

    data = da.from_zarr(abs_path)
    logger.debug(f"retrieved data: {data}")

    bf, fluo = data[int(index),int(chip_id)].compute()
    logger.debug(f'bf {bf.shape} fluo {fluo.shape}')

    return render_template(
        "image.html", 
        data=[{"name": "bf", "data": encode_base64(bf)}, 
            {"name": "fluo", "data": encode_base64(fluo, min=350, max=450)}
        ]
    )

@app.route("/img")
def show_img():
    return render_template("image.html")


if __name__ == '__main__':
    app.run(debug=True)
