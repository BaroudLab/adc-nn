from flask import Flask, render_template, request, make_response
import numpy as np
import os
import logging
import dask.array as da
from .tools import io
from .tools.io import (
    encode_base64,
    readdb,
    postdb,
    delete_feature,
    bf_fluo_2rgb,
    to8bits,
    get_centers,
    get_all_features,
    retrieve_random_droplet,
    retrieve_droplet,
    DATA_PREFIX,
    FLUO_MAX,
    FLUO_MIN
)
import subprocess

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

app = Flask(__name__)


@app.route("/")
def droplet_id():
    unique_antibiotic_types = readdb("SELECT DISTINCT antibiotic_type FROM datasets;")

    return render_template(
        "index.html",
        unique_antibiotic_types=unique_antibiotic_types,
    )

@app.route('/sort_features')
def sort_features():
    values = readdb(
        """SELECT
        id,
        name,
        'order',
        color
        FROM features
        ORDER BY "order"
        ;""",
        unique=False,
    )
    data = {"features": [{"id": i, "name": n, "order": o, "color": c} 
                         for i, n, o, c in values]}
    return render_template("sort_features.html", data=data)

@app.route('/update_order', methods=['POST'])
def update_order():
    order = request.json.get('order')
    if order:
        for sort_order, feature_id in enumerate(order):
            print(feature_id, sort_order)
            readdb(
                f"""
                UPDATE  features 
                SET "order"={sort_order} 
                WHERE id={feature_id}
                ;""")
    return 'OK'


@app.route('/update_color', methods=['POST'])
def update_color():
    feature_id = request.json.get('feature_id')
    color = request.json.get('color')
    if feature_id and color:
        readdb(
            f"""
            UPDATE  features 
            SET color="{color}"
            WHERE id={feature_id}
            ;"""
        )
    return 'OK'

@app.route("/ab_type/<antibiotic_type>")
def get_data(antibiotic_type):
    dates = readdb(
        f"SELECT DISTINCT date FROM datasets WHERE antibiotic_type='{antibiotic_type}';"
    )
    concentrations = [
        {
            "date": d,
            "antibiotic_type": antibiotic_type,
            "concentrations": [
                {"value": v, "unit": u, "stack_index": i, "path": p, "chip_id": c}
                for v, u, p, i, c in readdb(
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
        ;""",
                    unique=False,
                )
            ],
        }
        for d in dates
    ]
    return render_template("data.html", data=concentrations)


@app.route("/droplet/<chip_id>/<droplet_id>")
def get_droplet(chip_id, droplet_id):
    droplet = retrieve_random_droplet(
        chip_id=chip_id,
        droplet_id=droplet_id
    ) 
    
    return render_template(
        "images.html",
        data={"droplets": [droplet],
            "all_features": get_all_features()
        }
    )


@app.route("/droplets/<quantity>")
def get_droplets(quantity):
    chips = [{"chip_id": id, "path": path, "stack_index": s} 
             for id, path, s in readdb(
                """SELECT  chips.id, datasets.path, chips.stack_index
                FROM datasets
                JOIN chips
                ON chips.dataset_id = datasets.id;
                """,
                unique=False,
            )
    ]
    n_chips = len(chips)
    logger.debug(f"retrieved {n_chips} chips")

    selected = [
        {**chips[np.random.randint(n_chips)], "droplet_id": np.random.randint(500)} 
        for _ in range(int(quantity))
    ]

    droplets_dask = da.stack([
        retrieve_droplet(**chip, return_dask=True) 
        for chip in selected
    ])
    
    droplets_np = droplets_dask.compute()
    droplets = [
        {
            "rgb_image": io.encode_base64(io.to_rgb(bf_fluo)),
            "features": readdb(
                f"""
                    SELECT feature_id, value
                    FROM droplets
                    WHERE chip_id='{sel["chip_id"]}' and droplet_id={sel["droplet_id"]}
                    ;
                """, unique=False
            ),
            **sel} 
                for sel, bf_fluo in zip(selected, droplets_np) 
    ]

    return render_template(
        "images.html",
        data={"droplets": droplets,
            "all_features": get_all_features()
        }
    )


# @app.route("/verify/<quantity>")
# def check_droplets(quantity):
#     features = tr.get_unique_records()
#     droplets = tr.get_vectors(features=features)

#     droplets = [
#         {
#             "rgb_image": io.encode_base64(io.to_rgb(bf_fluo)),
#             "features": readdb(
#                 f"""
#                     SELECT feature_id, value
#                     FROM droplets
#                     WHERE chip_id='{sel["chip_id"]}' and droplet_id={sel["droplet_id"]};
#                 """, unique=False
#             ),
#             **sel} 
#                 for sel, bf_fluo in zip(selected, droplets_np) 
#     ]

#     return render_template(
#         "images.html",
#         data={"droplets": droplets,
#             "all_features": get_all_features()
#         }
#     )


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
            ;""",
        unique=False,
    )[0]

    _features = readdb(
        f"""SELECT
        id,
        droplet_id,
        feature_id
        FROM droplets
        WHERE
        chip_id='{chip_id}'
        ORDER BY "order"
        ;""",
        unique=False,
    )
    if _features:
        features = [
            {"table_id": table_id, "droplet_id": droplet_id, "feature_id": feature_id}
            for table_id, droplet_id, feature_id in _features
        ]
    else:
        features = []

    try:
        next_chip = readdb(
            f"""SELECT  
            chips.id
            FROM chips 
            WHERE 
            chips.dataset_id='{dataset_id}' and chips.stack_index='{stack_index+1}'
            ;""",
            unique=True,
        )[0]
        next_url = f"/chip/{next_chip}"
    except IndexError:
        next_url = f"/ab_type/{ab_type}"

    try:
        prev_chip = readdb(
            f"""SELECT  
            chips.id
            FROM chips 
            WHERE 
            chips.dataset_id='{dataset_id}' and chips.stack_index='{stack_index-1}'
            ;""",
            unique=True,
        )[0]
        prev_url = f"/chip/{prev_chip}"
    except IndexError:
        prev_url = f"/ab_type/{ab_type}"

    chip_path = path.replace(".crops.zarr", ".zarr")
    if not os.path.exists(chip_path):
         subprocess.run(['sshfs', "merlin.pub.pasteur.fr:Multicell", "/home/aaristov/Multicell/"])

    logger.debug(f"retrieved path: {chip_path}, stack_index: {stack_index}")

    abs_path = os.path.join(DATA_PREFIX, chip_path)
    logger.debug(f"abs_path {abs_path}")

    binning = 8
    data = da.from_zarr(os.path.join(abs_path, str(np.log2(binning).astype("int"))))
    print(f"retrieved data: {data}")

    subsampling = 1
    bf, fluo = data[int(stack_index), :2, ::subsampling, ::subsampling].compute()
    logger.debug(f"bf {bf.shape} fluo {fluo.shape}")

    rgb = bf_fluo_2rgb(bf=to8bits(bf), fluo=to8bits(fluo, imin=FLUO_MIN, imax=FLUO_MAX))
    return render_template(
        "chip.html",
        data={
            "imgData": {
                "name": "bf_fluo",
                "type": "data:image/jpeg;base64,",
                "value": encode_base64(rgb),
            },
            "meta": {
                "name": "meta",
                "centers": get_centers(binning=binning * subsampling),
                "path": chip_path,
                "chip_id": chip_id,
                "features": features,
                "stack_index": stack_index,
                "ab_type": ab_type,
                "ab_conc": ab_conc,
                "ab_unit": ab_unit,
                "min": FLUO_MIN,
                "max": FLUO_MAX,
                "next_chip": next_url,
                "prev_chip": prev_url,
                "back_url": f"/ab_type/{ab_type}",
                "all_features": get_all_features()
            },
        },
    )


@app.route("/droplet/feature/save", methods=["POST"])
def post():
    if request.method == "POST":
        status, err = postdb("droplets", **request.json)
        if status == "OK":
            return "OK"
        else:
            return {"status": "err", "err": err}


@app.route("/droplet/feature/remove", methods=["POST"])
def remove():
    """
    Removes the feature from the database
    """
    if request.method == "POST":
        print(request.json)
        chip_id = request.json["chip_id"]
        droplet_id = request.json["droplet_id"]
        feature_id = request.json["feature_id"]
        status, err = delete_feature(
            table="droplets", chip_id=chip_id, droplet_id=droplet_id, feature_id=feature_id
        )
        print(request.json)
        if status == "OK":
            return make_response("OK", f"deleted {droplet_id}")
        else:
            return make_response("err", str(err))


if __name__ == "__main__":
    app.run(debug=True)
