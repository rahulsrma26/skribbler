import os
import time
import subprocess
import numpy as np
from browser import Browser, Stage
from utils.svg import SVG
from utils.util import search_screen
from utils.resources import get_img


def main():
    p1 = Browser()
    url = p1.create(rounds=9, name='artist')
    p1.toggle_audio()
    # win = pygetwindow.getWindowsWithTitle('skribbl - Free Multiplayer Drawing & Guessing Game')[0]
    # print(win)

    p2 = Browser()
    p2.join(url, name='P2')
    p2.toggle_audio()

    while p1.num_players() != 2:
        time.sleep(0.5)

    p1.start()
    p2.load()
    w = p2.get_options()
    p2.pick_option(w[1])

    # p1.focus()
    time.sleep(1)
    path = r'C:\Program Files\obs-studio\bin\64bit'
    subprocess.Popen(f'"{path}\\obs64.exe"', cwd=path)
    time.sleep(3)
    x, y, a = search_screen(get_img('obs.png'))
    print(x, y, a)
    button = (x + 40, y + 40)

    SVG.HUMAN_ERROR = 1
    name = 'kirby'.lower()
    p2.set_current_word(name)
    p2.mouse.move_to(button).click()

    p2.action = True
    p2.draw(SVG.from_file(f'db/{name}.svg'), 45)
    p2.mouse.move_to(button).click()

    p2.close()
    p1.close()


if __name__ == '__main__':
    main()
