import os
import glob
import time
import logging
import cv2
import numpy as np
from browser import Browser
from utils.svg import SVG
from argparse import ArgumentParser, RawTextHelpFormatter


def _get_args():
    parser = ArgumentParser(
        prog=__name__, description=__doc__, formatter_class=RawTextHelpFormatter)
    parser.add_argument(
        'mode',
        choices=['dump', 'time', 'test', 'leak', 'xprt'],
        default='time', help='default is time')
    parser.add_argument(
        '-s', '--speed',
        type=int,
        default=50, help='speed of drawing (only spplies to time mode)')
    parser.add_argument(
        '-f', '--files',
        nargs='*', help='Force files to be included')
    parser.add_argument(
        '-td', '--tmpdir',
        default='tmp', help='Temporary directory to dump files')
    parser.add_argument(
        '-dd', '--datadir',
        default='db', help='SVG files directory')
    parser.add_argument(
        '-log', '--logging',
        default='WARNING', help='logging level')
    return parser.parse_args()


def get_path(args):
    path = os.path.join(args.tmpdir, args.mode)
    os.makedirs(path, exist_ok=True)
    if args.mode == 'dump':
        path = os.path.join(path, '*.png')
    elif args.mode == 'time':
        path = os.path.join(path, '*.txt')
    elif args.mode == 'test':
        path = os.path.join(path, '*.png')
    elif args.mode == 'leak':
        path = os.path.join(path, '*.txt')
    elif args.mode == 'xprt':
        path = os.path.join(path, '*.txt')
    else:
        print('Unsupported mode')
        exit()
    return path


def get_file(args):
    files = {}
    for fname in glob.glob(os.path.join(args.datadir, '*.svg')):
        name = os.path.splitext(os.path.basename(fname))[0]
        files[name] = fname
    modified = set(files.keys())
    for fname in glob.glob(get_path(args)):
        name = os.path.splitext(os.path.basename(fname))[0]
        if name in files:
            svg_time = os.path.getmtime(files[name])
            fil_time = os.path.getmtime(fname)
            if svg_time < fil_time:
                modified.remove(name)
        else:
            print(f'Warning!!! svg not found for {fname}')
    if args.files:
        modified.update(set(args.files))
    for name in sorted(list(modified)):
        yield name, files[name]


def save_text(file, text):
    with open(file, 'w') as f:
        f.write(text)


def draw(args, files, player):
    fpath = os.path.join(args.tmpdir, args.mode)
    if args.mode == 'dump':
        for _ in range(15):
            name, path = next(files)
            player.draw(SVG.from_file(path), 0)
            player.save_canvas(os.path.join(fpath, f'{name}.png'))
            player.clear_canvas()
            time.sleep(0.25)
    elif args.mode == 'time':
        name, path = next(files)
        player.set_current_word(name)
        start = time.time()
        player.draw(SVG.from_file(path), args.speed)
        delta = time.time() - start
        player.save_canvas(os.path.join(args.tmpdir, 'dump', f'{name}.png'))
        save_text(os.path.join(fpath, f'{name}.txt'), f'{delta:5.2f}\n')
        print(name, delta)
    elif args.mode == 'test':
        name, path = next(files)
        rows = []
        for _ in range(3):
            cols = []
            for __ in range(3):
                player.draw(SVG.from_file(path), 0)
                img = np.frombuffer(player.get_canvas(), np.uint8)
                cols.append(cv2.imdecode(img, cv2.IMREAD_COLOR))
                player.clear_canvas()
                time.sleep(0.25)
            rows.append(np.concatenate(cols, axis=1))
        img = np.concatenate(rows, axis=0)
        cv2.imwrite(os.path.join(fpath, f'{name}.png'), img)


def leak(original, path):
    gt = cv2.imread(original, cv2.IMREAD_COLOR)
    height, width, _ = gt.shape
    img = cv2.imread(path, cv2.IMREAD_COLOR)
    epsilon = (width // 100) * (height // 100)
    r = img.shape[0] // height
    c = img.shape[1] // width
    imgs = img.reshape(r, height, -1, width, 3).swapaxes(1,2).reshape(-1, height, width, 3)
    n = imgs.shape[0]
    diffs = []
    for k in range(3):
        a = dict(zip(*np.unique(gt[:,:,k], return_counts=True)))
        for i in range(n):
            b = dict(zip(*np.unique(imgs[i,:,:,k], return_counts=True)))
            errors = []
            for key in sorted(set(a.keys()).union(b.keys())):
                x, y = a.get(key, 0), b.get(key, 0)
                error = (max(x, y) - min(x, y)) / (max(x, y) + epsilon)
                errors.append(error)
            error = np.average(errors)
            diffs.append(error)
    return max(diffs)


def leak_test(args, files):
    worst = ['', 0]
    for name, _ in files:
        gt = os.path.join(args.tmpdir, 'dump', f'{name}.png')
        if not os.path.exists(gt):
            print(f'Warning!!! {gt} doesn\'t exits')
        test = os.path.join(args.tmpdir, 'test', f'{name}.png')
        if not os.path.exists(test):
            print(f'Warning!!! {test} doesn\'t exits')
        print(f'processing {name:20}, worst=({worst[1]:5.2f} {worst[0]:20})      ', end='\r')
        score = leak(gt, test)
        save_text(os.path.join(args.tmpdir, args.mode, f'{name}.txt'), f'{score:5.2f}\n')
        current = [name, score]
        if current[1] > worst[1]:
            worst = current
    print(f'{" ":80}')
    drawtime = []
    for path in glob.glob(get_path(args)):
        name, _ = os.path.splitext(os.path.basename(path))
        score = 1
        with open(path, 'r') as f:
            score = float(f.read())
        drawtime.append([name, score])
    for k, v in sorted(drawtime, key=lambda x: x[1], reverse=True)[:5]:
        print(f'{v:5.2f} {k}')


def export(args, files):
    for name, path in files:
        outpath = os.path.join(args.tmpdir, args.mode, f'{name}.txt')
        print(f'exporting {outpath:40}      ', end='\r')
        SVG.from_file(path).export(outpath)
    print(f'exported {" ":60}')


def main(args):
    logger = logging.getLogger(__file__)
    logger.setLevel(logging.getLevelName(args.logging))
    # logger.setLevel(logging.DEBUG)
    logging.basicConfig()

    files = get_file(args)
    if args.mode == 'leak':
        leak_test(args, files)
        return
    elif args.mode == 'xprt':
        export(args, files)
        return

    Browser.BENCHMARK = True
    p1 = Browser(logger=logger)
    url = p1.create(rounds=9, name='P1')
    p1.toggle_audio()

    p2 = Browser(logger=logger)
    p2.join(url, name='P2')
    p2.toggle_audio()

    while p1.num_players() != 2:
        time.sleep(0.5)

    while True:
        try:
            p1.start()
            p2.load()
            for _ in range(p1.rounds):
                w = p2.get_options()
                p2.pick_option(w[1])
                time.sleep(0.25)
                draw(args, files, p2)
                p1.type(w[1] + '\n')

                w = p1.get_options()
                p1.pick_option(w[1])
                time.sleep(0.25)
                draw(args, files, p1)
                p2.type(w[1] + '\n')
            p1.wait_till_overlay_goes_away()
        except StopIteration:
            break

    p2.close()
    p1.close()


if __name__ == '__main__':
    main(_get_args())
