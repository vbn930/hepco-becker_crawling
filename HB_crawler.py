from manager import log_manager
from manager import file_manager
from manager import web_driver_manager
from manager import translate_manager

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
import time

@dataclass
class Product:
    code: str
    name: str
    price: str
    description: str
    trans_description: str
    images: list
    make: str
    model: str
    category: str
    sub_category: str
    
class Hepco_Becker_Crawler:
    def __init__(self, logger: log_manager.Logger):
        self.file_manager = file_manager.FileManager()
        self.logger = logger
        self.driver_manager = web_driver_manager.WebDriverManager(self.logger)
        self.driver_manager.create_driver()
        self.driver_obj = self.driver_manager.drive_obj
        self.driver = self.driver_obj.driver
        self.file_manager.create_dir("./temp")
        self.file_manager.create_dir("./output")
        self.product_numbers = []
        self.products = []
        self.data = dict()
        self.data_init()
    
    def capitalize_words(self, s):
        # 빈 문자열이면 그대로 반환
        if not s:
            return s
        
        # 단어별로 분리하여 처리
        words = s.split()
        result = []
        for word in words:
            # 단어의 첫 글자를 대문자로, 나머지는 소문자로 변환
            capitalized_word = word.capitalize()
            result.append(capitalized_word)
        
        # 변환된 단어들을 공백으로 연결하여 반환
        return ' '.join(result)

    def get_init_settings_from_file(self, file_code):
        #cvs 파일에서 계정 정보, 브랜드, 브랜드 코드 가져오기
        data = pd.read_csv(f"./{file_code}_setting.csv")
        data.to_dict()
        
        setting_vals = []
        if file_code == "hb":
            if len(data["MAKE"]) != 0:
                setting_vals.append(data["MAKE"][0])
                setting_vals.append(data["MODEL"][0])
            else:
                setting_vals.append("")
                setting_vals.append("")
        elif file_code == "ls" or file_code == "pc":
            if len(data["CATEGORY"]) != 0:
                setting_vals.append(data["CATEGORY"][0])
                setting_vals.append(data["SUB CATEGORY"][0])
            else:
                setting_vals.append("")
                setting_vals.append("")
        
        self.logger.log_debug(f"Setting values : {setting_vals}")
        return setting_vals
        
    def data_init(self):
        self.data.clear()
        self.data["상품 코드"] = list()
        self.data["상품명"] = list()
        self.data["가격"] = list()
        self.data["대표 이미지"] = list()
        self.data["상세 이미지"] = list()
        self.data["설명"] = list()
        self.data["설명 번역"] = list()
        self.data["MAKE"] = list()
        self.data["MODEL"] = list()
        self.data["CATEGORY"] = list()
        self.data["SUBCATEGORY"] = list()

    def check_region_and_language(self):
        modal_element = self.driver.find_element(By.CLASS_NAME, "modal-body")
        ship_select = Select(modal_element.find_element(By.NAME, "countryId"))
        lang_select = Select(modal_element.find_element(By.NAME, "languageId"))
        
        ship_select.select_by_visible_text("Germany")
        lang_select.select_by_visible_text("English")

        self.driver.find_element(By.CLASS_NAME, "btn.btn-primary.btn-block.btn-primary.button-confirm.bst-country-check-accept-button").click()

        self.logger.log_debug("Modal popup check completed!")
    
    def get_items_from_categories(self, start_make="", start_model="", output_name=None):
        is_found_start_idx = False

        if start_make == "":
            is_found_start_idx = True
        
        make_select = Select(self.driver.find_elements(By.CLASS_NAME, "browser-default.custom-select.mmy-group")[0])

        make_options = [option.text for option in make_select.options if option.text != "Choose Brand"]

        for make_option in make_options:
            make_select = Select(self.driver.find_elements(By.CLASS_NAME, "browser-default.custom-select.mmy-group")[0])
            make_select.select_by_visible_text(make_option)
            self.logger.log_trace(f"Current make options : {make_option}")
            
            model_select = Select(self.driver.find_elements(By.CLASS_NAME, "browser-default.custom-select.mmy-group")[1])
            model_options = [option.text for option in model_select.options if option.text != "Choose Model"]
            self.logger.log_trace(f"Model option cnt: {len(model_options)}")

            for model_option in model_options:
                self.logger.log_info(f"Current make & model : {make_option} / {model_option}")

                make_select = Select(self.driver.find_elements(By.CLASS_NAME, "browser-default.custom-select.mmy-group")[0])
                make_select.select_by_visible_text(make_option)
                time.sleep(1)

                if start_make == make_option and start_model == model_option and is_found_start_idx == False:
                    is_found_start_idx = True

                if is_found_start_idx:
                    model_select = Select(self.driver.find_elements(By.CLASS_NAME, "browser-default.custom-select.mmy-group")[1])
                    model_select.select_by_visible_text(model_option)
                    time.sleep(5)

                    item_urls = self.get_item_list_in_category()
                    for item_url in item_urls:
                        item = self.get_item_information(item_url, make_option, model_option, output_name=output_name)
                        self.save_item_in_database(item)
                    self.save_database_to_excel(output_name=output_name)

                    self.driver.find_element(By.CLASS_NAME, "btn.btn-black.btn-mmy-clear").click()
                    time.sleep(5)

    def get_item_list_in_category(self):
        item_urls = []
        if self.driver_obj.is_element_exist(By.CLASS_NAME, "card-body"):
            product_card_elements = self.driver.find_elements(By.CLASS_NAME, "card-body")

            for product_card_element in product_card_elements:
                if self.driver_obj.is_element_exist(By.CLASS_NAME, "product-info", product_card_element):
                    item_name_element = product_card_element.find_element(By.CLASS_NAME, "product-info").find_element(By.CLASS_NAME, "product-name")
                    item_url = item_name_element.get_attribute("href")
                    item_name = item_name_element.get_attribute("title")
                    self.logger.log_info(f"Found item : {item_name}")
                    item_urls.append(item_url)
        
        return item_urls

    def get_item_information(self, item_url, make="", model="", categoty="", sub_category="", output_name=None):
        self.driver.get(item_url)
        item_name = self.driver.find_element(By.CLASS_NAME, "product-detail-name").text
        item_name = self.capitalize_words(item_name)
        item_code = self.driver.find_element(By.CLASS_NAME, "product-detail-ordernumber").text[3:]
        item_code = "hb" + item_code.replace(" ", "").replace("/", "-")
        item_price = self.driver.find_element(By.CLASS_NAME, "product-detail-price").text[1:-1]
        item_description = self.driver.find_element(By.CLASS_NAME, "product-detail-description-text").text.replace("\n","|")
        item_img_urls = []
        if self.driver_obj.is_element_exist(By.CLASS_NAME, "gallery-slider-thumbnails.tns-slider.tns-carousel.tns-subpixel.tns-calc.tns-horizontal"):
            img_elements = self.driver.find_element(By.CLASS_NAME, "gallery-slider-thumbnails.tns-slider.tns-carousel.tns-subpixel.tns-calc.tns-horizontal").find_elements(By.TAG_NAME, "img")
            for img_element in img_elements:
                img_url = img_element.get_attribute("src")
                item_img_urls.append(img_url)
        elif self.driver_obj.is_element_exist(By.TAG_NAME, "img", self.driver.find_element(By.CLASS_NAME, "base-slider.gallery-slider")):
            img_url = self.driver.find_element(By.CLASS_NAME, "base-slider.gallery-slider").find_element(By.TAG_NAME, "img").get_attribute("src")
            item_img_urls.append(img_url)

        item_img_names = []
        if len(item_img_urls) > 12:
            item_img_urls = item_img_urls[0:12]
        
        for i in range(len(item_img_urls)):
            item_img_url = item_img_urls[i]
            item_img_name = item_code + f"_{i+1}"
            item_img_names.append(item_img_name+".jpg")
            self.driver_manager.download_image(item_img_url, item_img_name, f"./output/{output_name}/images")
        self.logger.log_info(f"Item {item_name} crawling completed")

        item = Product(code=item_code, name=item_name, price=item_price, description=item_description, 
                       trans_description=translate_manager.translator(self.logger, "en", "ko", item_description),
                       images=item_img_names, make=make, model=model, category=categoty, sub_category=sub_category)
        # item = Product(code=item_code, name=item_name, price=item_price, description=item_description, 
        #                trans_description="",
        #                images=item_img_names, make=make, model=model, category=categoty, sub_category=sub_category)
        
        return item

    def save_item_in_database(self, item: Product):
        self.data["상품 코드"].append(item.code)
        self.data["상품명"].append(item.name)
        self.data["가격"].append(item.price)
        if len(item.images) != 0:
            self.data["대표 이미지"].append(item.images[0])
            self.data["상세 이미지"].append("|".join(item.images))
        else:
            self.data["대표 이미지"].append("")
            self.data["상세 이미지"].append("")
        self.data["설명"].append(item.description)
        self.data["설명 번역"].append(item.trans_description)
        self.data["MAKE"].append(item.make)
        self.data["MODEL"].append(item.model)
        self.data["CATEGORY"].append(item.category)
        self.data["SUBCATEGORY"].append(item.sub_category)

    def save_database_to_excel(self, output_name):
        self.file_manager.create_dir(f"./output/{output_name}")
        data_frame = pd.DataFrame(self.data)
        data_frame.to_excel(f"./output/{output_name}/{output_name}.xlsx", index=False)

    def start_category_crawling(self, output_name, start_make, start_model):
        self.logger.log_info(f"======Hepco&Becker Crawler======")
        url = "https://www.hepco-becker.de/en/"
        self.driver.get(url)
        self.check_region_and_language()
        self.get_items_from_categories(output_name=output_name, start_make=start_make, start_model=start_model)

    def get_category_links(self):
        category_infos = []
        category_elements = self.driver.find_elements(By.CLASS_NAME, "teaser-link")
        for category_element in category_elements:
            category_url = category_element.get_attribute("href")
            category_name = category_element.get_attribute("title")
            category_infos.append([category_name, category_url])

        return category_infos

    def start_sub_category_crawling(self, url, output_name, start_catrgory="", start_sub_category=""):
        self.logger.log_info(f"======Hepco&Becker Category Crawler======")
        self.driver.get(url)
        self.check_region_and_language()
        category_infos = self.get_category_links()
        # for category_url in category_urls:
        #     url = category_url[1]
        #     self.driver.get(url)
        #     category_infos += self.get_category_links()

        is_found_start_point = False
        if start_catrgory == "":
            is_found_start_point = True

        sub_category_infos = []
        for i in range(len(category_infos)):
            categoty_name = category_infos[i][0]
            categoty_url = category_infos[i][1]

            self.driver.get(categoty_url)
            category_temp_infos = self.get_category_links()

            for category_temp_info in category_temp_infos:
                #category, sub_category, url
                sub_category_infos.append([categoty_name, category_temp_info[0], category_temp_info[1]])

        for sub_category_info in sub_category_infos:
            url = sub_category_info[2]
            category_name = sub_category_info[0]
            sub_category_name = sub_category_info[1]
            self.logger.log_info(f"Current category : {category_name} / {sub_category_name}")
            if is_found_start_point == False and category_name == start_catrgory and sub_category_name == start_sub_category:
                is_found_start_point = True
            
            if is_found_start_point:
                page = 1
                item_urls = []
                self.driver.get(url)
                if self.driver_obj.is_element_exist(By.CLASS_NAME, "pagination-nav"):
                    while(True):
                        page_url = url + f"?order=topseller&p={page}"
                        self.driver.get(page_url)
                        self.logger.log_debug(f"Current page: {page_url}")
                        item_list = self.get_item_list_in_category()
                        if len(item_list) == 0:
                            break
                        item_urls += item_list
                        page += 1
                else:
                    item_urls = self.get_item_list_in_category()

                for item_url in item_urls:
                    item = self.get_item_information(item_url=item_url, categoty=category_name, sub_category=sub_category_name, output_name=output_name)
                    self.save_item_in_database(item)
                self.save_database_to_excel(output_name=output_name)
        pass