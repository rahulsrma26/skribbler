import math
import time
import random
import numpy as np
import pynput.mouse as pmouse
from utils.svg import SVG

class Mouse:
    MOVE_SPEED = 7
    HOLD_SPEED = 100
    DIST_CUTOFF = 10
    DEVIATION = 10

    def __init__(self):
        self.mouse = pmouse.Controller()

    def break_dist(self, old, new):
        dist = math.dist(old, new)
        if dist > self.DIST_CUTOFF:
            mx = int((old[0] + new[0]) / 2 + random.uniform(-SVG.HUMAN_ERROR, SVG.HUMAN_ERROR))
            my = int((old[1] + new[1]) / 2 + random.uniform(-SVG.HUMAN_ERROR, SVG.HUMAN_ERROR))
            return self.break_dist(old, (mx, my)) + self.break_dist((mx, my), new)
        return [new]

    def split(self, p1, p2):
        ratio = 0.2 + random.random() * 0.2
        point = p1*ratio + p2*(1-ratio) - p1
        theta = np.radians(random.randint(-self.DEVIATION, self.DEVIATION))
        c, s = np.cos(theta), np.sin(theta)
        c1 = np.array(((c, -s), (s, c))).dot(point) + p1
        ratio = 0.6 + random.random() * 0.2
        point = p1*ratio + p2*(1-ratio) - p2
        theta = np.radians(random.randint(-self.DEVIATION, self.DEVIATION))
        c, s = np.cos(theta), np.sin(theta)
        c2 = np.array(((c, -s), (s, c))).dot(point) + p2
        return [p1.tolist(), c1.tolist(), c2.tolist(), p2.tolist()]


    def get_position(self):
        return self.mouse.position


    def move_to(self, pos, wind=True):
        old = self.mouse.position
        if wind:
            dist = math.dist(old, pos)
            steps = int(0.5 + dist / self.DIST_CUTOFF)
            acc = [0]
            for i in range(steps):
                t = i / steps
                val = math.sin(3*(1 - t)*(1 - t))
                val *= 1.25 - random.random() / 2
                acc.append(acc[-1] + int(100*val))
            if acc[-1] > 0:
                curve = self.split(np.array(old), np.array(pos))
                for i, v in enumerate(acc):
                    t = v / acc[-1]
                    x, y = SVG._calc(curve, t)
                    if 0.3 < i/len(acc) < 0.7:
                        self.mouse.position = x + random.randint(-1, 1), y + random.randint(-1, 1)
                    else:
                        self.mouse.position = x, y
                    time.sleep(0.001)
            else:
                self.mouse.position = pos
                time.sleep(0.001)
        else:
            lines = self.break_dist(old, pos)
            n = len(lines)
            for i, (x, y) in enumerate(lines):
                dist = math.dist(self.mouse.position, (x, y)) / self.DIST_CUTOFF
                self.mouse.position = (x, y)
                t = i / n
                t = 1 - math.sin(3*(1 - t)*(1 - t))
                delay = (t + 0.1) * (1.25 - random.random() / 2) * dist * self.MOVE_SPEED
                time.sleep(max(1, delay) * 0.001)
        return self

    def press(self):
        self.mouse.press(pmouse.Button.left)
        time.sleep(self.HOLD_SPEED * 0.001)
        return self

    def release(self):
        self.mouse.release(pmouse.Button.left)
        time.sleep(self.HOLD_SPEED * 0.001)
        return self

    def click(self):
        self.mouse.press(pmouse.Button.left)
        time.sleep(self.HOLD_SPEED * 0.001)
        self.mouse.release(pmouse.Button.left)
        return self
