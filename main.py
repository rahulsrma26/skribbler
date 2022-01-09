from time import sleep

import numpy as np
import cv2
import pygetwindow
from PIL import ImageGrab
from pynput import keyboard

from utils import util
from utils.resources import get_img
from PIL import ImageGrab

break_program = False
def on_press(key):
    global break_program
    print (key)
    if key == keyboard.Key.esc:
        print ('esc pressed')
        break_program = True
        return False


WIN_WIDTH, WIN_HEIGHT = 1200, 800
COLORS_ROWS, COLORS_COLS = 2, 11
CAN_WIDTH, CAN_HEIGHT = 620, 460


class Canvas:
    COLORS_IMG = 'colors.png'
    BRUSHES_IMG = 'brushes.png'
    CANVAS_IMG = 'canvas.png'

    def __init__(self) -> None:
        self.colors = self._get_image(Canvas.COLORS_IMG)
        self.brushes = self._get_image(Canvas.BRUSHES_IMG)
        self.canvas = self._get_image(Canvas.CANVAS_IMG)
        self.canvas = (self.canvas[0] + 8, self.canvas[1] + 8)
        self.palette = self._get_palette()
        self.pen = 2


    def _get_image(self, name):
        ans = util.search_screen(get_img(name))
        if ans[2] < 0.99:
            print(f'{name} not found {ans[2]}')
            quit()
        print(f'{name} found at {ans}')
        return ans[:2]

    def _get_palette(self):
        img = get_img('colors.png', mode=cv2.IMREAD_COLOR)
        palette = cv2.resize(get_img('colors.png', mode=cv2.IMREAD_COLOR), (COLORS_COLS, COLORS_ROWS), interpolation = cv2.INTER_AREA)
        return palette.reshape(-1, 3)

    def _select_color(self, number):
        x, y = number % COLORS_COLS, number // COLORS_COLS
        util.click(self.colors[0] + 24*x + 12, self.colors[1] + 24*y + 12)

    def _select_brush(self, i):
        self.pen = [2, 5, 14, 30][i]
        util.click(self.brushes[0] + 50*i + 12, self.brushes[1] + 12)

    def _break_row(self, row):
        result = []
        start, col = 0, row[0]
        for i, v in enumerate(row):
            if v != col:
                result.append((start, i, col))
                start, col = i, v
        result.append((start, len(row), col))
        return result

    def draw(self, img, brush=1):
        self._select_brush(brush)
        max_width, max_height = CAN_WIDTH // self.pen, CAN_HEIGHT // self.pen
        AR = max_width / max_height
        h, w = img.shape[:2]
        ar = w / h
        if ar > AR:
            img = cv2.resize(img, (max_width, int(max_width * h / w)), interpolation = cv2.INTER_NEAREST)
        else:
            img = cv2.resize(img, (int(max_height * w / h), max_height), interpolation = cv2.INTER_NEAREST)
        # img = cv2.bilateralFilter(img, 9, 75, 75)
        img = util.quantize(img, self.palette)
        print('drawing', img.shape)

        with keyboard.Listener(on_press=on_press) as listener:
            # Collect events until released
            for y, row in enumerate(img):
                for s, e, c in self._break_row(row):
                    if c:
                        self._select_color(c)
                        util.hline(self.canvas[0] + s * self.pen, self.canvas[0] + e * self.pen, self.canvas[1] + y * self.pen)
                if break_program:
                    listener.join()
                    quit()
            listener.stop()
            listener.join()


def main():
    win = pygetwindow.getWindowsWithTitle('skribbl - Free Multiplayer Drawing & Guessing Game')[0]
    win.size = (WIN_WIDTH, WIN_HEIGHT)
    win.activate()
    sleep(0.9)
    print(win.title)

    game = Canvas()
    # util.click(canvas[0], canvas[1])
    # game._select_color(5)
    # util.hline(game.canvas[0], game.canvas[0] + 150, game.canvas[1] + 10, 50)

    # url = 'https://www.seekpng.com/png/detail/30-303468_peacock-peacock-clipart.png'
    # img = util.image_from_url(url)
    # if not img:
    #     print('Image not loaded')
    #     quit()

    img = np.array(ImageGrab.grabclipboard())
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    print('image', img.shape)
    game.draw(img)

if __name__ == '__main__':
    main()

# guys I have written a program that can draw. Just testing please dont mind