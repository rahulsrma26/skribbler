import math
from collections import deque

import cv2
import numpy as np

from utils.svg import SVG
from utils.palette import Palette

pal = Palette.from_file('resources/skribbl.gpl')

def draw(img, svg, speed=0):
    sizes = np.array([3, 7, 19, 39], dtype=np.int32)
    for obj in svg.paths:
        # print(obj)
        if obj.color:
            three = deque(maxlen=3)
            for points in svg.get_points(obj):
                cur = points[0]
                if not three or three[-1] != cur:
                    three.append(cur)
                for pos in points[1:]:
                    three.append(pos)
                    col = pal[pal.nearest(obj.color)].tolist()
                    # col = pal[np.random.randint(0, 21)].tolist()
                    brush = sizes[np.argmin(np.abs(sizes - obj.thickness))]
                    cv2.line(img, cur, pos, col, brush)
                    if speed:
                        dist = math.dist(cur, pos)
                        delay = int(max(speed/10, speed * min(1, dist/ 20)))
                        delay = speed
                        if len(three) == 3:
                            a = max(1, math.dist(three[0], three[1]))
                            b = max(1, math.dist(three[1], three[2]))
                            c = max(1, math.dist(three[2], three[0]))
                            # print((a*a + b*b - c*c)/(2*a*b))
                            ang = np.arccos(max(-1, min(1, (a*a + b*b - c*c)/(2*a*b))))
                            delay = max(1, int(2 * delay * (1 - ang / (2*math.pi))))
                        if cv2.waitKey(delay) == 27:
                            return
                        cv2.imshow('img', img)
                    cur = pos
        if obj.fill:
            col = pal[pal.nearest(obj.fill)].tolist()
            # print((obj.cx, obj.cy), col)
            cv2.floodFill(img, None, (obj.cx, obj.cy), col)
            if speed:
                cv2.imshow('img', img)
                if cv2.waitKey(speed) == 27:
                    return
    return img

svg = SVG.from_file('db/pepper.svg'.lower())
# print(svg)
width = svg.right - svg.left
height = svg.bottom - svg.top
img = np.ones((height, width, 3), dtype=np.uint8) * 255

# cv2.line(img, (23, 40), (541, 15), 0, 2)
# drawb(img, svg.paths[1].path[1])

draw(img, svg)
# i1 = np.concatenate((draw(np.copy(img), svg), draw(np.copy(img), svg)), axis=1)
# i2 = np.concatenate((draw(np.copy(img), svg), draw(np.copy(img), svg)), axis=1)
# img = np.concatenate((i1, i2), axis=0)

cv2.imshow('img', img)
cv2.waitKey(0)

# img = np.zeros((460, 620))
# img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
# print('image', img.shape)
# img = cv2.bilateralFilter(img, 9, 75, 75)
# CAN_WIDTH, CAN_HEIGHT = 620, 460
# PEN_SIZE = 2
# max_width, max_height = CAN_WIDTH // PEN_SIZE, CAN_HEIGHT // PEN_SIZE
# h, w = img.shape[:2]
# if w >= h:
#     img = cv2.resize(img, (max_width, int(max_width * h / w)), interpolation = cv2.INTER_NEAREST)
# else:
#     img = cv2.resize(img, (int(max_height * w / h), max_height), interpolation = cv2.INTER_NEAREST)

# res = util.quantize(img, palette)
# for y, row in enumerate(res):
#     for x, val in enumerate(row):
#         img[y,x,:] = palette[val]

# url = 'https://clipart.world/wp-content/uploads/2020/11/Thanksgiving-Turkey-clipart-transparent.png'
# resp = requests.get(url, stream=True).raw
# img = np.asarray(bytearray(resp.read()), dtype="uint8")
# img = cv2.imdecode(img, cv2.IMREAD_COLOR)
# cv2.imshow('image', img)
# cv2.waitKey(0)

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
