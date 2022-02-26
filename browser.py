import random
import time
import base64
import logging
from enum import Enum
import numpy as np
import clipboard
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common import exceptions
from selenium.webdriver.support.color import Color
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC

from utils.svg import SVG
from utils.palette import Palette
# from utils.util import nearest_color
from utils.mouse import Mouse


class Stage(Enum):
    AD = 0
    LOADING = 1
    LOGIN = 2
    TRANSITION = 3
    GUSSING = 4
    SELECTION = 5
    DRAWING = 6


def coord(location: dict):
    return np.array([location['x'], location['y']])


class Browser:
    URL = 'https://skribbl.io/'
    TIME_LIMIT = 10
    WAIT_TIME = 0.5
    TYPE_SPEED = 0.1
    count = 0
    BENCHMARK = False
    LOGIN = 'loginAvatarCustomizeContainer'


    def __init__(self, action=False, logger=None):
        self.logger = logger or logging.getLogger(__file__)
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_experimental_option("excludeSwitches", ['enable-automation'])
        self.driver = webdriver.Chrome('chromedriver.exe', options=chrome_options)
        self.driver.set_window_size(1380, 920)
        self.driver.set_window_position(1380 * Browser.count, 10)
        self.offsetX = self.driver.execute_script('return window.outerWidth - window.innerWidth;') // 2
        self.offsetY = self.driver.execute_script('return window.outerHeight - window.innerHeight;') - self.offsetX
        self.offset = np.array([self.offsetX, self.offsetY])
        self.mouse = Mouse()
        self.action = action
        Browser.count += 1
        self.options = self.word = None
        self.rounds = self.draw_time = None
        self.loaded = False
        self.resert_draw(0)


    def focus(self):
        self.driver.execute_script(f'window.focus()')


    def resize(self):
        self.driver.set_window_size(1380, 920)


    def go_to_url(self, url=None, retries=5):
        if not url:
            url = self.URL
        for _ in range(retries):
            try:
                self.logger.debug('setting url to %s', url)
                self.driver.get(url)
                self.logger.debug('locating element %s', self.LOGIN)
                elem = WebDriverWait(self.driver, 10).until(
                    EC.visibility_of_element_located((By.ID, self.LOGIN)))
                self.logger.debug('Element %s located', self.LOGIN)
                return elem
            except exceptions.TimeoutException:
                print(f'Loading {url} failed. Retrying ...')
                time.sleep(1)
        return None


    def _click(self, elem):
        if self.action:
            self.mouse.move_to(self._get_location(elem))
        elem.click()


    def _type(self, elem, text):
        if self.action:
            self.mouse.move_to(self._get_location(elem)).click()
        for c in text:
            elem.send_keys(c)
            time.sleep(self.TYPE_SPEED)


    def _choose(self, elem, option):
        if self.action:
            self.mouse.move_to(self._get_location(elem)).click()
        Select(elem).select_by_visible_text(option)


    def create(self, rounds=3, draw_time=180, custom_words='', custom_only=False, name=None):
        if not self.go_to_url():
            print("Error!!! Check internet!!!")
            quit()
        self.rounds = rounds
        self.draw_time = draw_time
        time.sleep(self.WAIT_TIME)

        if name:
            elem = WebDriverWait(self.driver, self.TIME_LIMIT).until(
                EC.visibility_of_element_located((By.ID, 'inputName')))
            self._type(elem, name)

        elem = WebDriverWait(self.driver, self.TIME_LIMIT).until(
            EC.visibility_of_element_located((By.ID, 'buttonLoginCreatePrivate')))
        self._click(elem)
        time.sleep(self.WAIT_TIME)

        elem = WebDriverWait(self.driver, self.TIME_LIMIT).until(
            EC.visibility_of_element_located((By.ID, 'lobbySetRounds')))
        self._choose(elem, str(rounds))

        elem = WebDriverWait(self.driver, self.TIME_LIMIT).until(
            EC.visibility_of_element_located((By.ID, 'lobbySetDrawTime')))
        self._choose(elem, str(draw_time))

        if custom_words:
            self.driver.find_element(By.ID, 'lobbySetCustomWords').send_keys(custom_words)
            if custom_only:
                self._click(self.driver.find_element(By.ID, 'lobbyCustomWordsExclusive'))

        self._click(self.driver.find_element(By.ID, 'inviteCopyButton'))
        return clipboard.paste()


    def join(self, url=None, name=None):
        if not self.go_to_url(url):
            print("Error!!! Check internet!!!")
            quit()
        time.sleep(self.WAIT_TIME)

        if name:
            elem = WebDriverWait(self.driver, self.TIME_LIMIT).until(
                EC.visibility_of_element_located((By.ID, 'inputName')))
            self._type(elem, name)

        elem = WebDriverWait(self.driver, self.TIME_LIMIT).until(
            EC.visibility_of_element_located((By.ID, 'formLogin'))).find_element(
            By.TAG_NAME, 'button')
        self._click(elem)

        time.sleep(self.WAIT_TIME)


    def stage(self):
        try:
            # try:
            #     if self.driver.find_element(By.ID, 'aipPrerollContainer').is_displayed():
            #         self.loaded = False
            #         return Stage.AD
            # except exceptions.NoSuchElementException:
            #     pass
            if self.driver.find_element(By.ID, 'loginAvatarCustomizeContainer').is_displayed():
                self.loaded = False
                return Stage.LOGIN
            try:
                if not self.driver.find_element(By.ID, 'screenGame').is_displayed():
                    self.loaded = False
                    return Stage.AD
            except exceptions.NoSuchElementException:
                pass
            self.load()
            overlay = self.driver.find_element(By.ID, 'overlay')
            if overlay.is_displayed():
                if overlay.find_element(By.CLASS_NAME, 'wordContainer').is_displayed():
                    return Stage.SELECTION
                else:
                    return Stage.TRANSITION
            elif self.toolbar.is_displayed():
                return Stage.DRAWING
            else:
                return Stage.GUSSING
        except exceptions.NoSuchElementException:
            pass
        return Stage.LOADING


    def _load_colors(self, toolbar):
        colors = {}
        for e in toolbar.find_elements(By.CLASS_NAME, 'colorItem'):
            idx = int(e.get_attribute('data-color'))
            colors[idx] = e
        return colors


    def _create_palette(self, colors):
        palette = []
        for i in sorted(colors.keys()):
            col = Color.from_string(colors[i].value_of_css_property('background-color'))
            palette.append([col.blue, col.green, col.red])
        return Palette(palette)


    def _load_tools(self, toolbar):
        tools = {}
        elem = toolbar.find_element(By.CLASS_NAME, 'containerTools')
        for e in elem.find_elements(By.CLASS_NAME, 'tool'):
            name = e.get_attribute('data-tool')
            tools[name] = e
            if 'toolActive' in e.get_attribute('class'):
                self.current_tool = name
        return tools


    def _load_brushes(self, toolbar):
        convert = {'0': 3, '0.15': 7, '0.45': 19, '1': 39}
        brushes = {}
        elem = toolbar.find_element(By.CLASS_NAME, 'containerBrushSizes')
        for e in elem.find_elements(By.CLASS_NAME, 'brushSize'):
            s = e.get_attribute('data-size')
            brushes[convert[s]] = e
        return brushes


    def get_current_word(self):
        elem = WebDriverWait(self.driver, self.TIME_LIMIT).until(
                EC.visibility_of_element_located((By.ID, 'currentWord')))
        if not elem.text:
            time.sleep(0.5)
            return self.get_current_word()
        return elem.text


    def set_current_word(self, word):
        element = self.driver.find_element_by_id('currentWord')
        self.driver.execute_script(f'arguments[0].innerText = "{word}"', element)


    def load(self):
        self.logger.debug('loading elements %s', self.loaded)
        if not self.loaded:
            time.sleep(0.5)
            self.toolbar = self.driver.find_element(By.CLASS_NAME, 'containerToolbar')
            self.colors = self._load_colors(self.toolbar)
            self.palette = self._create_palette(self.colors)
            self.tools = self._load_tools(self.toolbar)
            self.brushes = self._load_brushes(self.toolbar)
            self.canvas = self.driver.find_element(By.ID, 'canvasGame')
            self.chat = WebDriverWait(self.driver, self.TIME_LIMIT).until(
                EC.element_to_be_clickable((By.ID, 'inputChat')))
            self.loaded = True
            self.logger.debug('Elements loaded ...')


    def save_canvas(self, filepath):
        with open(filepath, 'wb') as f:
            f.write(self.get_canvas())


    def get_canvas(self):
        canvas_base64 = self.driver.execute_script("return arguments[0].toDataURL('image/png').substring(21);", self.canvas)
        return base64.b64decode(canvas_base64)


    def delay(self, multiplier):
        if self.speed:
            if not self.BENCHMARK:
                multiplier = (multiplier / 2) + random.random() * multiplier
            time.sleep(self.speed * 0.001 * multiplier)


    def resert_draw(self, speed):
        self.current_tool = self.current_brush = self.current_color = None
        self.speed = speed


    def _get_location(self, elem, center = True):
        window = coord(self.driver.get_window_position())
        if center:
            window += np.array([elem.size['width'], elem.size['height']]) // 2
        elem = coord(elem.location)
        return window + elem + self.offset


    def clear_canvas(self):
        elem = self.driver.find_element(By.ID, 'buttonClearCanvas')
        if self.action:
            self.mouse.move_to(self._get_location(elem)).click()
        else:
            elem.click()


    def changeTool(self, name):
        if self.current_tool != name:
            self.logger.debug(f'Changing tool from {self.current_tool} to {name}')
            if self.action:
                self.mouse.move_to(self._get_location(self.tools[name])).click()
            else:
                self.delay(5)
                self.tools[name].click()
            self.current_tool = name


    def changeBrush(self, size):
        if self.current_brush != size:
            self.logger.debug(f'Changing brush from {self.current_brush} to {size}')
            if self.action:
                self.mouse.move_to(self._get_location(self.brushes[size])).click()
            else:
                self.delay(5)
                self.brushes[size].click()
            self.current_brush = size


    def changeColor(self, idx):
        if self.current_color != idx:
            self.logger.debug(f'Changing color from {self.current_color} to {idx}')
            if self.action:
                self.mouse.move_to(self._get_location(self.colors[idx])).click()
            else:
                self.delay(5)
                self.colors[idx].click()
            self.current_color = idx


    def draw(self, svg, speed=0):
        self.resert_draw(speed)
        sizes = np.array(sorted(self.brushes.keys()), dtype=np.int32)
        size_multiplier = [1.0, 0.9, 0.8, 0.7]
        canvas = self._get_location(self.canvas, False)
        cmx, cmy = self.canvas.size['width'] // 2, self.canvas.size['height'] // 2
        try:
            for obj in svg.paths:
                if not self.toolbar.is_displayed():
                    return
                ac = None
                if obj.color:
                    self.changeTool('pen')
                    brush_size = np.argmin(np.abs(sizes - obj.thickness))
                    self.changeBrush(sizes[brush_size])
                    self.changeColor(self.palette.nearest(obj.color))
                    line_boost = 0.75 if svg.is_solo_line(obj) else 1
                    dur = int(self.speed * size_multiplier[brush_size] * line_boost)
                    # print(svg.is_solo_line(obj), brush_size, dur)
                    if not self.action:
                        ac = ActionChains(self.driver, duration=dur).move_to_element(self.canvas)
                        ac = ac.move_by_offset(-cmx, -cmy)
                    lst = 0, 0
                    for lines in svg.get_points(obj):
                        if not self.toolbar.is_displayed():
                            return
                        cur = lines[0]
                        if self.action:
                            self.mouse.move_to(cur + canvas).press()
                        else:
                            dx, dy = cur[0] - lst[0], cur[1] - lst[1]
                            ac = ac.move_by_offset(dx, dy).click_and_hold()
                        lst = cur
                        for cur in lines[1:]:
                            if self.action:
                                self.mouse.move_to(cur + canvas, False)
                            else:
                                dx, dy = cur[0] - lst[0], cur[1] - lst[1]
                                ac = ac.move_by_offset(dx, dy)
                            lst = cur
                    if self.action:
                        self.mouse.release()
                    else:
                        ac.release().perform()
                if obj.fill:
                    self.changeTool('fill')
                    self.changeColor(self.palette.nearest(obj.fill))
                    if self.action:
                        self.mouse.move_to(np.array([obj.cx, obj.cy]) + canvas).click()
                    else:
                        self.delay(5)
                        ac = ActionChains(self.driver, duration=speed).move_to_element(self.canvas)
                        ac.move_by_offset(obj.cx - cmx, obj.cy - cmy).click().perform()
        except exceptions.ElementNotInteractableException:
            pass


    def start(self):
        elem = WebDriverWait(self.driver, self.TIME_LIMIT).until(
            EC.visibility_of_element_located((By.ID, 'buttonLobbyPlay')))
        self._click(elem)
        time.sleep(self.WAIT_TIME)
        self.load()


    def toggle_audio(self):
        elem = WebDriverWait(self.driver, self.TIME_LIMIT).until(
            EC.visibility_of_element_located((By.ID, 'audio')))
        self._click(elem)


    def num_players(self):
        return len(self.driver.find_element(
            By.ID, 'containerLobbyPlayers').find_elements(
                By.CLASS_NAME, 'lobbyPlayer'))


    def get_options(self, wait=True):
        overlay = self.driver.find_element(By.ID, 'overlay')
        while wait and overlay.find_element(By.CLASS_NAME, 'text').text != 'Choose a word':
            time.sleep(self.WAIT_TIME)
        elem = overlay.find_element(By.CLASS_NAME, 'wordContainer')
        self.options = [(e.text, e) for e in elem.find_elements(By.CLASS_NAME, 'word')]
        return [e[0] for e in self.options]


    def set_options_color(self, available):
        for op, check in zip(self.options, available):
            color = 'green' if check else 'red'
            self.driver.execute_script(f'arguments[0].style.backgroundColor = "{color}"', op[1])


    def save_options(self, path='tmp/history.txt'):
        with open(path, 'a+') as f:
            for t, _ in self.options:
                f.write(t + '\n')


    def wait_till_overlay_goes_away(self):
        overlay = self.driver.find_element(By.ID, 'overlay')
        while overlay.is_displayed():
            time.sleep(self.WAIT_TIME)


    def pick_option(self, word, wait=True):
        if self.options:
            for k, v in self.options:
                if k == word:
                    if self.action:
                        self.mouse.move_to(self._get_location(v)).click()
                    else:
                        self.delay(5)
                        v.click()
                    self.wait_till_overlay_goes_away()
                    self.word = word
                    return


    def focus_chat(self):
        self.chat.click()


    def type(self, text):
        self._type(self.chat, text)


    def close(self):
        self.driver.close()


    def is_opened(self):
        try:
            self.driver.current_url # or driver.title
            return True
        except exceptions.WebDriverException as e:
            print('!!! Window Closed !!!', e)
            return False


    def test_draw(self):
        canvas = self._get_location(self.canvas, False)
        line = np.array([600, 0])
        for i in range(10):
            v = np.array([20, 40 + i*40])
            self.mouse.move_to(canvas + v).press().move_to(canvas + v + line).release()


if __name__ == '__main__':
    # player = Browser()
    # player.go_to_url()
    # time.sleep(2)
    # # player.check()
    # # player.create(rounds=7, custom_words='a,b,c,d', custom_only=True)
    # # player.join()
    # player.close()

    p1 = Browser()
    url = p1.create(rounds=2)
    p2 = Browser()
    p2.join(url)

    while p1.num_players() != 2:
        time.sleep(0.5)

    p1.start()
    # p1.palette.save('resources/new.gpl')
    w = p2.get_options()
    p2.pick_option(w[1])
    time.sleep(0.5)
    # p2.test()
    name = 'apple'.lower()
    pos = p2.mouse.mouse.position
    start = time.time()
    svg = SVG.from_file(f'db/{name}.svg')
    # svg = SVG.import_from(f'tmp/xprt/{name}.txt')
    print(time.time() - start)
    # p2.test_draw()
    p2.draw(svg, 45)
    p2.mouse.move_to(pos)
    p1.type(w[1] + '\n')
    time.sleep(5)
    # p2.clear_canvas()
    # p2.save_canvas(f'tmp/dump/{name}.png')
    p2.close()
    p1.close()