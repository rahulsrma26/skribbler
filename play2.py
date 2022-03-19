import os
import glob
import random
import numpy as np
import PySimpleGUI as sg
from utils.svg import SVG
from browser import Browser, Stage
from utils.word_db import WordDB
from selenium.common import exceptions


def make_window(win, words, cols=2, contains=None):
    position = tuple(np.array(win.CurrentLocation(True)) + np.array([0, 25+win.Size[1]]))
    layout = []
    if contains:
        f1 = [w for w in words if w.startswith(contains)]
        f2 = [w for w in words if (not w.startswith(contains) and contains in w)]
        words = f1 + f2
    n = len(words)
    if not n:
        return None
    for i in range(0, n, cols):
        layout.append([sg.Button(w, font=('Courier', 10), pad=(0,0)) for w in words[i:i+cols]])
    return sg.Window('Words', layout, finalize=True, location=position, no_titlebar=True, margins=(0,0), use_default_focus=False)


def IButton(*args, **kwargs):
    return sg.Col([[sg.Button(*args, **kwargs)]], pad=(0,0))


def main_window():
    button = sg.Button('Open Browser', key='__OPEN__')
    slider = sg.Slider(range=(0, 100), orientation='h',
        default_value=55, enable_events=True, disable_number_display=True, key='__SPEED__')
    stext = sg.Text(str(slider.DefaultValue), key='__STEXT__')
    search = sg.Input(size=(520, 1), enable_events=True, key='__INPUT__')
    choices = [IButton(f'C{i}', visible=False, size=(20, 1), key=f'__C{i}__') for i in range(3)]
    layout = [
        [button, sg.Button('Draw?', key='__DRAW?__'), slider, stext],
        [search],
        choices
    ]
    window = sg.Window('Skribbler', layout, size=(520, 80), location=(1380, 0), finalize=True, margins=(0,0))
    window['__INPUT__'].bind('<Return>', 'ENTER__')
    return window, choices


def main():
    Browser.TYPE_SPEED = 0
    win1, choices = main_window()
    win1.read(timeout=50)
    db = WordDB('resources/words.csv')
    files = {}
    for filepath in glob.glob("db/*.svg"):
        name, _ = os.path.splitext(os.path.basename(filepath))
        files[name] = filepath

    win2, words, game = None, [], None
    stage, last_stage, last_word = '', '', ''
    while True:
        window, event, values = sg.read_all_windows(timeout=500)
        if event == sg.WIN_CLOSED or event == 'Exit':
            window.close()
            if window == win2:
                win2 = None
            elif window == win1:
                break
        try:
            stage = game.stage() if game else ''
        except exceptions.WebDriverException:
            game, stage = None, ''
            win1['__OPEN__'].update(text='Open Browser')
        win1.set_title(f'Skribbler [{stage}]')
        if stage == Stage.GUSSING:
            word = game.get_current_word()
            if word != last_word:
                words = db.find(word, display=False)
                n = len(words[0])
                col = (55 if n > 4 else 50) // n
                if win2:
                    win2.close()
                win2 = make_window(win1, words, cols=col, contains='')
                win1.TKroot.focus_force()
                win1['__INPUT__'].update(value='')
                win1['__INPUT__'].set_focus(True)
                last_word = word
        elif stage != last_stage:
            if stage == Stage.SELECTION:
                options = game.get_options(False)
                print('Options:', ' | '.join(options))
                for op, btn in zip(options, choices):
                    col = 'green' if db.image(op) in files else 'red'
                    btn.Rows[0][0].update(visible=True, text=op, button_color=col)
            elif stage == Stage.DRAWING:
                for btn in choices:
                    btn.Rows[0][0].update(visible=False)
                word = game.get_current_word()
                if word != last_word and db.image(word) in files:
                    game.resize()
                    speed = win1['__SPEED__'].DefaultValue
                    game.draw(SVG.from_file(files[db.image(word)]), speed)
                    last_word = word
        elif win2:
            win2.close()
            win2 = None
        if event == '__OPEN__':
            if game:
                game.close()
                game = None
                win1['__OPEN__'].update(text='Open Browser')
            else:
                game = Browser(update_counter=False)
                game.go_to_url('https://skribbl.io/')
                win1['__OPEN__'].update(text='Close Browser')
                window.TKroot.focus_force()
        elif event == '__SPEED__':
            win1['__STEXT__'].update(value=int(values['__SPEED__']))
        elif event.startswith('__C') and game:
            for btn in choices:
                btn.Rows[0][0].update(visible=False)
            game.pick_option(options[int(event[3])])
        elif event == '__DRAW?__':
            game.type('draw' + ('?' * random.randint(3, 10)) + '\n')
        elif event == '__INPUT__':
            if win2:
                win2.close()
            win2 = make_window(win1, words, cols=col, contains=values['__INPUT__'])
            window.TKroot.focus_force()
            win1['__INPUT__'].set_focus(True)
        elif event == '__INPUT__ENTER__' and win2:
            game.type(win2.Rows[0][0].ButtonText + '\n')
        elif not event.startswith('__') and game:
            game.type(event + '\n')
        elif event != '__TIMEOUT__':
            print(event)
        last_stage = stage

    # window.close()


if __name__ == '__main__':
    main()
