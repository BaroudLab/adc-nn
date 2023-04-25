from . import io
import numpy as np


def get_unique_records():
    unique_records = [io.retrieve_random_droplet(c, d)["rgb_image"]
        for c, d in io.readdb("""
            SELECT DISTINCT 
            droplets.chip_id, 
            droplets.droplet_id, 
            FROM droplets;
        """, unique=False)]
    return unique_records


def get_vector_size():
    return io.readdb("SELECT COUNT(*) FROM features;")[0]


def get_vectors(features: dict):
    fs = get_vector_size()
    return [{"vector": features_to_vector(fs, rec["features"]), **rec} 
            for rec in features
            ]


def features_to_vector(vector_size: int, features: list):
    vector = np.zeros((vector_size, ))
    for f in features:
        vector[f["id"]-1] = 1
    return vector
