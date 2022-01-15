import cv2
import numpy as np
import requests
import mss
import pynput.mouse as pmouse


def search_screen(template, monitor=0, match=cv2.TM_CCOEFF_NORMED):
    with mss.mss() as sct:
        img = np.array(sct.grab(sct.monitors[monitor]))
        img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        res = cv2.matchTemplate(img_gray, template, match)
        w, h = res.shape[::-1]
        idx = np.argmax(res)
        return int(idx % w), int(idx//w), np.max(res)


def click(x, y, speed=1):
    mouse = pmouse.Controller()
    mouse.position = (x, y)
    mouse.press(pmouse.Button.left)
    cv2.waitKey(speed)
    mouse.release(pmouse.Button.left)

def hline(x1, x2, y, speed=1):
    mouse = pmouse.Controller()
    mouse.position = (x1, y)
    mouse.press(pmouse.Button.left)
    cv2.waitKey(speed)
    mouse.move(x2 - x1, 0)
    cv2.waitKey(speed)
    mouse.release(pmouse.Button.left)

def quantize(im, palette):
    dims = list(im.shape)
    flt = im.astype(np.float) / 255.0
    flt = np.repeat(flt, palette.shape[0], axis=1).reshape([dims[0],dims[1],-1,3])
    pal = palette.astype(float) / 255.0
    diff = flt - pal
    res = np.linalg.norm(diff, axis=3)
    bst = np.argmin(res, axis=2)
    return bst

def nearest_color(col, palette):
    flt = np.array(col, dtype=np.float) / 255.0
    flt = np.tile(flt, palette.shape[0]).reshape([-1, 3])
    pal = palette.astype(float) / 255.0
    return np.argmin(np.linalg.norm(flt - pal, axis=1))

def image_from_url(url):
    resp = requests.get(url, stream=True).raw
    print(resp.read())
    img = np.asarray(bytearray(resp.read()), dtype="uint8")
    return cv2.imdecode(img, cv2.IMREAD_COLOR)
