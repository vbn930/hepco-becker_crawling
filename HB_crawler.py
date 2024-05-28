from manager import log_manager
from manager import file_manager
from manager import web_driver_manager

from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from dataclasses import dataclass
import pandas as pd
import datetime

@dataclass
class Product:
    code: str
    name: str
    price: str
    dealer_price: str
    description: str
    trans_description: str
    images: list
    option_name: str
    option_value: str
    make: str
    model: str
    year: str

@dataclass
class ShopCatrgory:
    make: str
    model: str
    year: str
    href: str
    
class HB_Crawler:
    def __init__(self, logger: log_manager.Logger):
        self.file_manager = file_manager.FileManager()
        self.logger = logger
        self.driver_manager = web_driver_manager.WebDriverManager(self.logger)
        self.driver = self.driver_manager.create_driver()
        self.file_manager.create_dir("./temp")
        self.file_manager.create_dir("./output")
        self.product_numbers = []
        self.products = []
        self.data = dict()
        self.data_init()

    def get_init_settings_from_file(self):
        #cvs 파일에서 계정 정보, 브랜드, 브랜드 코드 가져오기
        data = pd.read_csv("./setting.csv").fillna(0)
        account = data["account"].to_list()
        account.append(0)
        account = account[0:account.index(0)]

        start_maker = data["start_maker"].to_list()
        start_maker.append(0)
        start_maker = start_maker[0:start_maker.index(0)]
        
        if len(start_maker) == 0:
            return account[0], account[1], 0, 0, 0
        
        start_model = data["start_model"].to_list()
        start_model.append(0)
        start_model = start_model[0:start_model.index(0)]

        start_year = data["start_year"].to_list()
        start_year.append(0)
        start_year = start_year[0:start_year.index(0)]
        
        if not isinstance(start_year[0], str):
            if isinstance(start_year[0], int):
                return account[0], account[1], start_maker[0], start_model[0], str(start_year[0])
            elif isinstance(start_year[0], float):
                return account[0], account[1], start_maker[0], start_model[0], str(int(start_year[0]))
            else:
                return account[0], account[1], start_maker[0], start_model[0], start_year[0]
        else:
            return account[0], account[1], start_maker[0], start_model[0], start_year[0]
        
    def data_init(self):
        self.data.clear()
        self.data["상품 코드"] = list()
        self.data["상품명"] = list()
        self.data["정상가"] = list()
        self.data["대표 이미지"] = list()
        self.data["상세 이미지"] = list()
        self.data["옵션명"] = list()
        self.data["옵션 내용"] = list()
        self.data["설명"] = list()
        self.data["설명 번역"] = list()
        self.data["MAKE"] = list()
        self.data["MODEL"] = list()
        self.data["YEAR"] = list()
        self.data["CATEGORY"] = list()
        self.data["SUBCATEGORY"] = list()
        
    def get_shop_categories(self, start_make, start_model, start_year):
        is_found_start_idx = False
        shop_categories = []