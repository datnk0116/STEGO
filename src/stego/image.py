from pathlib import Path
import numpy as np
from PIL import Image

def decode_blue3(path):
    with Image.open(path) as im:
        pixels = np.asarray(im.convert('RGB'), dtype=np.int16)
    h, w, _ = pixels.shape
    colors, counts = np.unique(pixels.reshape(-1, 3), axis=0, return_counts=True)
    base = colors[int(np.argmax(counts))].astype(np.int16)
    attempts = []
    for n in range(2, min(w, h) + 1):
        cw, ch = w // n, h // n
        chars = []
        for i in range(n):
            block = pixels[i*ch:(i+1)*ch, i*cw:(i+1)*cw]
            value = int((block - base).sum())
            if not 0 <= value <= 0x10ffff:
                chars = []
                break
            chars.append(chr(value))
        candidate = ''.join(chars)
        if candidate:
            attempts.append({'length': n, 'candidate': candidate})
        if candidate.startswith('byuctf{') and candidate.endswith('}') and all(c.isalnum() or c in '_{}' for c in candidate):
            return {'flag': candidate, 'format_valid': True, 'attempts': attempts}
    return {'flag': None, 'format_valid': False, 'attempts': attempts}
