import os
import glob
import time
import logging
from colorama import Fore
from utils.svg import SVG
from browser import Browser, Stage
from utils.word_db import WordDB


def main():
    logging.basicConfig()
    logger = logging.getLogger(__file__)
    # logger.setLevel(logging.DEBUG)
    # formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    # fh = logging.FileHandler('tmp/log.txt')
    # fh.setLevel(logging.DEBUG)
    # fh.setFormatter(formatter)
    # logger.addHandler(fh)
    # ch = logging.StreamHandler()
    # ch.setLevel(logging.INFO)
    # ch.setFormatter(formatter)
    # logger.addHandler(ch)
    # logging.getLogger().handlers = []

    # filename='tmp/log.txt', level=logging.DEBUG,

    db = WordDB('resources/words.csv')
    files = {}
    for filepath in glob.glob("db/*.svg"):
        name, _ = os.path.splitext(os.path.basename(filepath))
        files[name] = filepath

    def color(name, image):
        return (Fore.GREEN if image in files else Fore.RED) + name + Fore.RESET + ' '

    def check(image):
        return image in files

    game = Browser(logger=logger)
    game.go_to_url('https://skribbl.io/')

    last_stage, last_word = '', ''
    while game.is_opened():
        time.sleep(0.5)
        stage = game.stage()
        if stage == Stage.GUSSING:
            word = game.get_current_word()
            if word != last_word:
                game.focus_chat()
                db.find(word)
                last_word = word
        elif stage != last_stage:
            if stage == Stage.SELECTION:
                options = game.get_options(False)
                print(''.join([color(w, db.image(w)) for w in options]))
                game.set_options_color([check(db.image(w)) for w in options])
            elif stage == Stage.DRAWING:
                word = game.get_current_word()
                print(f'drawing {word}')
                if word != last_word and db.image(word) in files:
                    time.sleep(1)
                    game.resize()
                    game.draw(SVG.from_file(files[db.image(word)]), 50)
                    last_word = word
            else:
                print(stage)
        last_stage = stage


if __name__ == '__main__':
    main()

# fall minigolf ruby anchor pepper fortress skateboard sushi bird
# band-aid pond lake pool playground kiss evolution piano ninja diploma mr. bean room spine
# usb gift notebook headband popeye wallpaper spaghetti|pasta dominoes
# corn graffiti cage sonic cone king magic|wizard|gandalf chin onion