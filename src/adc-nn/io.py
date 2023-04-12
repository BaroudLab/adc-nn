import numpy as np
import io
from PIL import Image
import base64


def encode_base64(image, min=None, max=None):
    imin = image.min() if min is None else min
    imax = image.max() if max is None else max
    norm01 = (image - imin) / (imax-imin)
    norm01[norm01 > 1] = 1
    norm01[norm01 < 0] = 0
    image_8bit = (norm01 * 255).astype(np.uint8)

    image_pil = Image.fromarray(image_8bit, mode='L').convert('RGB')

    with io.BytesIO() as buffer:
        image_pil.save(buffer, format='JPEG')
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return image_base64
