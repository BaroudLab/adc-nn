import numpy as np
import os
import io as _io
from PIL import Image
import base64
import sqlite3
import logging
import dask.array as da

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


DB_ADDRESS = "database.db"
DATA_PREFIX = "/home/aaristov/Multicell/"

FLUO_MIN = 380
FLUO_MAX = 600

def retrieve_random_droplet(chip_id, droplet_id=np.random.randint(500) + 1):
    out = readdb(f"""
            SELECT 
            datasets.path, 
            chips.stack_index 
            FROM chips
            JOIN datasets
            ON datasets.id=chips.dataset_id
            WHERE chips.id='{chip_id}';
        """, unique=False)[0]
    print(out)
    path, stack_index = out
    rgb = retrieve_droplet(path, stack_index, droplet_id)
    features = readdb(f"""
        SELECT feature_id, value
        FROM droplets
        WHERE chip_id='{chip_id}' and droplet_id={droplet_id};
    """, unique=False)
    return {
        "chip_id": chip_id,
        "droplet_id": droplet_id,
        "features": [
            {"feature_id": f, "value": v}
            for f, v in features
        ],
        "rgb_image": encode_base64(rgb),
    }


def retrieve_droplet(path, stack_index, droplet_id, return_dask=False, **kwargs):

    abs_path = os.path.join(DATA_PREFIX, path)
    logger.debug(f"abs_path {abs_path}")

    data = da.from_zarr(abs_path)
    logger.debug(f"retrieved data: {data}")

    assert (ddd := int(droplet_id) - 1) >= 0,\
          f"droplet_id should be between 1 and 500, got {droplet_id}"
    bf_fluo = data[ddd, int(stack_index)]
    if return_dask:
        return bf_fluo
    return to_rgb(bf_fluo.compute())

def to_rgb(bf_fluo):
    bf, fluo = bf_fluo
    logger.debug(f"bf {bf.shape} fluo {fluo.shape}")
    rgb = bf_fluo_2rgb(bf=to8bits(bf), fluo=to8bits(fluo, imin=FLUO_MIN, imax=FLUO_MAX))
    return rgb

def readdb(query, unique=True):
    with sqlite3.connect(DB_ADDRESS) as conn:
        cursor = conn.cursor()
        cursor.execute(query)
        values = cursor.fetchall()
    if unique:
        return [v[0] for v in values]
    return values


def delete_feature(table, chip_id, droplet_id, feature_id):
    print("delete feature", table, chip_id, droplet_id, feature_id)
    try:
        with sqlite3.connect(DB_ADDRESS) as conn:
            cursor = conn.cursor()
            query = f"""
            DELETE FROM {table}
            WHERE 
            chip_id='{chip_id}' AND droplet_id={droplet_id} AND feature_id={feature_id}
            """
            cursor.execute(query)
        return "OK", None
    except sqlite3.OperationalError as e:
        return "error", e


def postdb(table, **kwargs):
    try:
        with sqlite3.connect(DB_ADDRESS) as conn:
            cursor = conn.cursor()
            fields = ",".join(map(str, kwargs.keys()))
            print(fields)
            values = ",".join(
                map(
                    lambda x: str(x) if isinstance(x, int) else f"'{x}'",
                    kwargs.values(),
                )
            )
            print(values)
            query = f"""
            INSERT INTO {table}
            ({fields})
            VALUES
            ({values});
            """
            print(query)
            cursor.execute(query)
        return "OK", None
    except sqlite3.OperationalError as e:
        return "error", e

def get_all_features():

    _features = readdb(
        """SELECT
            id,
            name,
            color
            FROM features;
        """,
        unique=False,
    )
    if _features:
        features = [
                {"id": id, "name": name, "color": color}
            for id, name, color in _features
        ]
    else:
        features = []
    return features


def get_centers(binning=2):
    db_centers = readdb("SELECT id, y,x, binning, size FROM centers;", unique=False)
    out = [
        {
            "id": id,
            "y": y * b / binning,
            "x": x * b / binning,
            "bin": binning,
            "size": size * b / binning,
            "color": "#ffffff60",
        }
        for id, y, x, b, size in db_centers
    ]
    print(f"get centers with binning {binning}, raw data bin {db_centers[0][3]}")
    return out


def bf_fluo_2rgb(bf, fluo):
    """
    creates rgb stack combining bf as grayscale and fluo as cyan
    params:
    -------
    bf: 2D np.ndarray of type 'uint8'
    fluo: 2D np.ndarray of type 'uint8'
    """
    r = bf
    g = np.stack((bf, fluo)).max(axis=0)
    b = g
    return np.dstack((r, g, b)).astype("uint8")


def encode_base64(image, imin=None, imax=None):
    """
    Convert to 8 bits if needed and encode the result in base64
    """
    image_8bit = (
        image if image.dtype == np.uint8 else to8bits(image, imin=imin, imax=imax)
    )
    mode = "L" if image.ndim == 2 else "RGB"

    image_pil = Image.fromarray(image_8bit, mode=mode).convert("RGB")

    with _io.BytesIO() as buffer:
        image_pil.save(buffer, format="JPEG")
        image_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return image_base64


def to8bits(image, imin=None, imax=None):
    """
    Converting to 8 bits
    If min, max not provided, they are calculated automatically
    """
    imin = image.min() if imin is None else imin
    imax = image.max() if imax is None else imax
    norm01 = (image - imin) / (imax - imin)
    norm01[norm01 > 1] = 1
    norm01[norm01 < 0] = 0
    return (norm01 * 255).astype(np.uint8)
