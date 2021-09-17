import subprocess
import json
from selenium import webdriver



class CustomMessageProcessor():

    def __init__(self, data_bytes):
        decoded = data_bytes.decode('utf-8')
        self.message_dict = json.loads(decoded)

    def process(self):
        
        if self.message_dict['type'] == 'display_request':
            orientation_request = self.message_dict['orientation']
            url = self.message_dict['url']
            response = self.play_video(url, orientation_request)

            return response
    
    def play_video(self, url, orientation):

        # # change display orientation
        # if orientation == 'v':
        #     x = subprocess.run(['xrandr', '-o', 'right'])
        # else:
        #     x = subprocess.run(['xrandr', '-o', 'normal'])

        # connect to site
        options = webdriver.ChromeOptions()

        options.add_argument('--start-maximized')
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-automation")
        options.add_argument("--start-fullscreen")
        options.add_argument("--kiosk")
        options.add_experimental_option("excludeSwitches" , ["enable-automation"])
        options.add_experimental_option("excludeSwitches" , ["enable-automation","load-extension"])

        driver = webdriver.Chrome(options=options) #Would like chrome to start in fullscreen
        driver.get(url)

        response = 'success'.encode(encoding='UTF-8')
        return response