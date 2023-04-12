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
def droplet_id():
    unique_antibiotic_types = readdb('SELECT DISTINCT antibiotic_type FROM datasets;')

    return render_template('index.html', 
                           unique_antibiotic_types=unique_antibiotic_types,
                           )

@app.route('/ab_type/<antibiotic_type>')
def get_data(antibiotic_type):
    dates = readdb(f"SELECT DISTINCT date FROM datasets WHERE antibiotic_type='{antibiotic_type}';")
    concentrations = [{
        "date": d, 
        "antibiotic_type": antibiotic_type, 
        "concentrations": [{
            "value": v, 
            "unit": u, 
            "stack_index": i,
            "path": p,
            "chip_id": c
        } for v,u,p,i,c in readdb(
        f"""SELECT  
            chips.concentration, 
            datasets.unit, 
            datasets.path, 
            chips.stack_index,
            chips.id
            FROM datasets 
            JOIN chips 
            ON chips.dataset_id = datasets.id
            WHERE 
            datasets.antibiotic_type='{antibiotic_type}' AND
            datasets.date='{d}'
        ;""", unique=False)]        
    } for d in dates]
    return render_template("data.html", data=concentrations)

@app.route("/droplet/<chip_id>/<droplet_id>")
def get_images(chip_id, droplet_id):
    path, stack_index, ab_type, ab_conc, ab_unit = readdb(
            f"""SELECT  
            datasets.path, 
            chips.stack_index,
            datasets.antibiotic_type,
            chips.concentration,
            datasets.unit
            FROM datasets 
            JOIN chips 
            ON chips.dataset_id = datasets.id
            WHERE 
            chips.id='{chip_id}'
            ;""", unique=False)[0]
    logger.debug(f"retrieved path: {path}, chip_id: {chip_id}")

    abs_path = os.path.join(DATA_PREFIX, path)
    logger.debug(f"abs_path {abs_path}")

    data = da.from_zarr(abs_path)
    logger.debug(f"retrieved data: {data}")

    bf, fluo = data[int(droplet_id),int(stack_index)].compute()
    logger.debug(f'bf {bf.shape} fluo {fluo.shape}')

    return render_template(
        "image.html", 
        data=[{"name": "bf", "data": encode_base64(bf)}, 
            {"name": "fluo",
             "data": encode_base64(fluo, min=(mi:=400), max=(ma:=600)), 
             "min": mi, 
             "max": ma, 
             "ab_type": ab_type,
             "ab_conc": ab_conc,
             "ab_unit": ab_unit,
             "url_next": f"/droplet/{chip_id}/{int(droplet_id)+1}",
             "url_prev": f"/droplet/{chip_id}/{int(droplet_id)-1}",
             "back_url": f"/ab_type/{ab_type}"}
        ]
    )

@app.route("/chip/<chip_id>")
def get_chip(chip_id):
    dataset_id, path, stack_index, ab_conc, ab_type, ab_unit = readdb(
            f"""SELECT  
            datasets.id, 
            datasets.path, 
            chips.stack_index,
            chips.concentration,
            datasets.antibiotic_type,
            datasets.unit
            FROM datasets 
            JOIN chips 
            ON chips.dataset_id = datasets.id
            WHERE 
            chips.id='{chip_id}'
            ;""", unique=False)[0]
    try:
        next_chip = readdb(f"""SELECT  
            chips.id
            FROM chips 
            WHERE 
            chips.dataset_id='{dataset_id}' and chips.stack_index='{stack_index+1}'
            ;""", unique=True)[0]
        next_url = f"/chip/{next_chip}"
    except IndexError:
        next_url = f"/ab_type/{ab_type}"
    
    try:
        prev_chip = readdb(f"""SELECT  
            chips.id
            FROM chips 
            WHERE 
            chips.dataset_id='{dataset_id}' and chips.stack_index='{stack_index-1}'
            ;""", unique=True)[0]
        prev_url = f"/chip/{prev_chip}"
    except IndexError:
        prev_url = f"/ab_type/{ab_type}"

    chip_path = path.replace(".crops.zarr", ".zarr")
    logger.debug(f"retrieved path: {chip_path}, stack_index: {stack_index}")

    abs_path = os.path.join(DATA_PREFIX, chip_path)
    logger.debug(f"abs_path {abs_path}")

    data = da.from_zarr(os.path.join(abs_path, "3"))
    print(f"retrieved data: {data}")

    bf, fluo = data[int(stack_index), :2, ::2, ::2].compute()
    logger.debug(f'bf {bf.shape} fluo {fluo.shape}')

    return render_template(
        "chip.html", 
        data=[{"name": "bf", "data": encode_base64(bf)}, 
            {"name": "fluo", 
             "data": encode_base64(fluo, min=(mi:=400), max=(ma:=600)), 
             "path": chip_path,
             "stack_index": stack_index,
             "ab_type": ab_type,
             "ab_conc": ab_conc,
             "ab_unit": ab_unit,
             "min": mi, 
             "max": ma, 
             "next_chip": next_url,
             "prev_chip": prev_url,
             "back_url": f"/ab_type/{ab_type}"}
        ]
    )

@app.route("/img")
def show_img():
    return render_template("image.html")


if __name__ == '__main__':
    app.run(debug=True)
