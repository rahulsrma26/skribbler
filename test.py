from time import sleep

import numpy as np
import cv2
import requests
from PIL import ImageGrab

from utils import util
from utils.resources import get_img


img = get_img('colors.png', mode=cv2.IMREAD_COLOR)
COLORS_ROWS, COLORS_COLS = 2, 11
palette = cv2.resize(img, (COLORS_COLS, COLORS_ROWS), interpolation = cv2.INTER_AREA)
palette = palette.reshape(-1, 3)
print(palette)

img = np.array(ImageGrab.grabclipboard())
img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
print('image', img.shape)
img = cv2.bilateralFilter(img, 9, 75, 75)
CAN_WIDTH, CAN_HEIGHT = 620, 460
PEN_SIZE = 2
max_width, max_height = CAN_WIDTH // PEN_SIZE, CAN_HEIGHT // PEN_SIZE
h, w = img.shape[:2]
if w >= h:
    img = cv2.resize(img, (max_width, int(max_width * h / w)), interpolation = cv2.INTER_NEAREST)
else:
    img = cv2.resize(img, (int(max_height * w / h), max_height), interpolation = cv2.INTER_NEAREST)

res = util.quantize(img, palette)
for y, row in enumerate(res):
    for x, val in enumerate(row):
        img[y,x,:] = palette[val]

# url = 'https://clipart.world/wp-content/uploads/2020/11/Thanksgiving-Turkey-clipart-transparent.png'
# resp = requests.get(url, stream=True).raw
# img = np.asarray(bytearray(resp.read()), dtype="uint8")
# img = cv2.imdecode(img, cv2.IMREAD_COLOR)
cv2.imshow('image', img)
cv2.waitKey(0)

# COLORS_ROWS, COLORS_COLS = 2, 11
# img = get_img('colors.png', mode=cv2.IMREAD_COLOR)

# COLORS_ROWS, COLORS_COLS = 2, 11

# palette = cv2.resize(img, (COLORS_COLS, COLORS_ROWS), interpolation = cv2.INTER_AREA)
# print(palette.shape)
# palette = palette.reshape(-1, 3)
# # palette = palette.reshape(-1, 1, 3)
# # cv2.imwrite('test.png', palette)

# cv2.imshow('image', img)
# cv2.waitKey(0)

# r = quantize(img, palette)
# print(r)
