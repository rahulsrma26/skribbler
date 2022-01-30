import time
import clipboard
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common import exceptions
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class Browser:
    URL = 'https://skribbl.io/'
    TIME_LIMIT = 10
    WAIT_TIME = 0.5
    TYPE_SPEED = 0.1
    count = 0


    def __init__(self):
        self.driver = webdriver.Chrome('chromedriver.exe')
        self.driver.set_window_size(1200, 800 + 45)
        self.driver.set_window_position(1200 * Browser.count, 50)
        Browser.count += 1
        self.options = self.word = None
        self.rounds = self.draw_time = None


    def go_to_url(self, url, retries=5):
        for _ in range(retries):
            try:
                self.driver.get(url)
                elem = WebDriverWait(self.driver, 10).until(
                    EC.visibility_of_element_located((By.ID, 'loginAvatarCustomizeContainer')))
                return elem
            except exceptions.TimeoutException:
                print(f'Loading {url} failed. Retrying ...')
                time.sleep(1)
        return None


    def create(self, rounds=3, draw_time=180):
        if not self.go_to_url(self.URL):
            print("Error!!! Check internet!!!")
            quit()
        self.rounds = rounds
        self.draw_time = draw_time

        time.sleep(self.WAIT_TIME)
        WebDriverWait(self.driver, self.TIME_LIMIT).until(
            EC.visibility_of_element_located((By.ID, 'buttonLoginCreatePrivate'))).click()

        time.sleep(self.WAIT_TIME)
        Select(WebDriverWait(self.driver, self.TIME_LIMIT).until(
            EC.visibility_of_element_located((By.ID, 'lobbySetRounds')))
        ).select_by_visible_text(str(rounds))

        Select(WebDriverWait(self.driver, self.TIME_LIMIT).until(
            EC.visibility_of_element_located((By.ID, 'lobbySetDrawTime')))
        ).select_by_visible_text(str(draw_time))

        self.driver.find_element(By.ID, 'inviteCopyButton').click()
        return clipboard.paste()


    def join(self, url=None):
        if not url:
            url = self.URL
        if not self.go_to_url(url):
            print("Error!!! Check internet!!!")
            quit()

        time.sleep(self.WAIT_TIME)
        WebDriverWait(self.driver, self.TIME_LIMIT).until(
            EC.visibility_of_element_located((By.ID, 'formLogin'))).find_element(
            By.TAG_NAME, 'button').click()


    def start(self):
        WebDriverWait(self.driver, self.TIME_LIMIT).until(
            EC.visibility_of_element_located((By.ID, 'buttonLobbyPlay'))).click()
        time.sleep(self.WAIT_TIME)


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
                    v.click()
                    self.wait_till_overlay_goes_away()
                    self.word = word
                    return


    def type(self, text):
        elem = self.driver.find_element(By.ID, 'inputChat')
        for c in text:
            elem.send_keys(c)
            time.sleep(self.TYPE_SPEED)


    def close(self):
        self.driver.close()


    def is_opened(self):
        try:
            self.driver.current_url # or driver.title
            return True
        except exceptions.WebDriverException as e:
            print('!!! Window Closed !!!', e)
            return False
