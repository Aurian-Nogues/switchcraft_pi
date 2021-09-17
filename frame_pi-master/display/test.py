import pathlib
import os
# from selenium.webdriver.chrome.options import Options  
from selenium import webdriver
import time

url = 'https://frame-zero.herokuapp.com/player/4/0x60F80121C31A0d46B5279700f9DF786054aa5eE5/913180/h/auto/100%25/%23000000'

# chrome_options = Options()
# chrome_options.add_experimental_option("useAutomationExtension", False)
# chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
# chrome_options.add_argument("--start-fullscreen");
# chrome_options.add_argument("--kiosk")

# # driver_path = os.path.join(os.getcwd(), 'display', 'chromedriver')
# # driver_path = '/usr/lib/chromium-browser/chromedriver'
# # print(driver_path)

# print('a')
# driver = webdriver.Chrome(options=chrome_options)
# # browser = webdriver.Chrome(executable_path = '/usr/lib/chromium-browser/chromedriver')
# browser.get('www.google.com')
# print('b')

# driver_path = os.path.join(os.getcwd(), 'display', 'geckodriver')

# driver = webdriver.Firefox()
# driver.get('http://raspberrypi.stackexchange.com/')

# chromeOptions = Options()
# chromeOptions.add_argument("--kiosk")
# chromeOptions.addArguments("disable-infobars")
# driver = webdriver.Chrome(chrome_options=chromeOptions) #Would like chrome to start in fullscreen
# driver.get("https://www.google.com")

options = webdriver.ChromeOptions()

# options.add_argument('--no-sandbox')
# options.add_argument('--disable-dev-shm-usage')

options.add_argument('--start-maximized')
options.add_argument("--disable-extensions")
options.add_argument("--disable-automation")
options.add_argument("--start-fullscreen")
options.add_argument("--kiosk")
options.add_experimental_option("excludeSwitches" , ["enable-automation"])
options.add_experimental_option("excludeSwitches" , ["enable-automation","load-extension"])
options.add_experimental_option('useAutomationExtension', False)

driver = webdriver.Chrome(options=options) #Would like chrome to start in fullscreen
driver.get(url)
