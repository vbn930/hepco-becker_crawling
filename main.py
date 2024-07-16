import HB_crawler
from manager import log_manager
from manager import file_manager as FM
import datetime

# pyinstaller -n "Hepco&Becker Crawler ver1.3" --clean --onefile main.py

# pyinstaller -n "Hepco&Becker Luggage-Systems Crawler ver1.4" --clean --onefile main.py

# pyinstaller -n "Hepco&Becker Protection-Comfort Crawler ver1.4" --clean --onefile main.py

global log_level
log_level = log_manager.LogType.BUILD

def start_luggage_systems_crawling():
    now = datetime.datetime.now()
    year = f"{now.year}"
    month = "%02d" % now.month
    day = "%02d" % now.day
    output_name = f"{year+month+day}_HB_LS"

    file_manager = FM.FileManager()

    file_manager.create_dir(f"./output/{output_name}")
    file_manager.create_dir(f"./output/{output_name}/images")
    
    logger = log_manager.Logger(log_level)
    crawler = HB_crawler.Hepco_Becker_Crawler(logger)
    ls_url = "https://www.hepco-becker.de/en/luggage-systems"
    setting_vals = crawler.get_init_settings_from_file("ls")
    crawler.start_sub_category_crawling(url=ls_url, output_name=output_name, start_catrgory=setting_vals[0], start_sub_category=setting_vals[1])

def start_protection_comfort_crawling():
    now = datetime.datetime.now()
    year = f"{now.year}"
    month = "%02d" % now.month
    day = "%02d" % now.day
    output_name = f"{year+month+day}_HB_PC"

    file_manager = FM.FileManager()

    file_manager.create_dir(f"./output/{output_name}")
    file_manager.create_dir(f"./output/{output_name}/images")
    
    logger = log_manager.Logger(log_level)
    crawler = HB_crawler.Hepco_Becker_Crawler(logger)
    pc_url = "https://www.hepco-becker.de/en/schutz"
    setting_vals = crawler.get_init_settings_from_file("pc")
    crawler.start_sub_category_crawling(url=pc_url, output_name=output_name, start_catrgory=setting_vals[0], start_sub_category=setting_vals[1])

def start_category_crawling():
    now = datetime.datetime.now()
    year = f"{now.year}"
    month = "%02d" % now.month
    day = "%02d" % now.day
    output_name = f"{year+month+day}_HB"

    file_manager = FM.FileManager()

    file_manager.create_dir(f"./output/{output_name}")
    file_manager.create_dir(f"./output/{output_name}/images")
    
    logger = log_manager.Logger(log_level)
    crawler = HB_crawler.Hepco_Becker_Crawler(logger)
    setting_vals = crawler.get_init_settings_from_file("hb")
    crawler.start_category_crawling(output_name, setting_vals[0], setting_vals[1])

# start_category_crawling()
# start_luggage_systems_crawling()
start_protection_comfort_crawling()

end_msg = input("프로그램을 종료하시려면 엔터키를 눌러주세요.")