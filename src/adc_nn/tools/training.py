"""
This module halp to prepare the data for training: 
retrieveing images and making vectors with features
"""

from . import io
import numpy as np


def get_unique_records():
    """
    Retrieving base64 images of the droplets
    """
    unique_records = [io.retrieve_random_droplet(c, d)["rgb_image"]
        for c, d in io.readdb("""
            SELECT DISTINCT 
            chip_id, 
            droplet_id
            FROM droplets;
        """, unique=False)]
    return unique_records


def get_vector_size():
    """
    Getting total number of unique features 
    """
    return io.readdb("SELECT COUNT(*) FROM features;")[0]


def get_vectors(features: dict):
    """
    Adds vectors to feature list
    """
    fs = get_vector_size()
    return [{"vector": features_to_vector(fs, rec["features"]), **rec} 
            for rec in features
            ]


def features_to_vector(vector_size: int, features: list):
    """
    Converts list of features to the vector of 0 and 1.
    """
    vector = np.zeros((vector_size, ))
    for f in features:
        vector[f["id"]-1] = 1
    return vector
