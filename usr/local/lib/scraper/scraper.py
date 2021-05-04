#!/usr/bin/env python3
"""
Description:
    Example scraper.

Usage:
    scraper.py [options]
    scraper.py (-h | --help)

Options:
    -h,--help               Show this screen.
    --config=<config>       Path to config file [default: /usr/local/etc/scraper.conf]
    --headless              Runs Firefox in headless mode

Description:
    This is an example of a simple webscraper. It opens a wikipedia page,
    and retrieves the headline. It then prints the headline to the
    standard output. If it cannot locate headline after 5
    tries in a row, the script quits.
"""

# 3rd party
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from loguru import logger
from docopt import docopt

# built-ins
from pathlib import Path
import configparser
import sys
import time


def start_firefox(run_headless=True):
    options = webdriver.FirefoxOptions()
    options.headless = run_headless
    driver = webdriver.Firefox(options=options,
                               service_log_path="/tmp/geckodriver.log")
    driver.set_window_position(0, 0)
    driver.set_window_size(1920, 1080)
    return driver


@logger.catch()
def retrieve_text_from_page(driver, url, page_element_css_id):
    driver.get(url)
    WebDriverWait(driver, timeout=15).until(
        ec.presence_of_element_located((By.ID, page_element_css_id))
    )
    elements = driver.find_elements_by_class_name(page_element_css_id)
    if elements:
        txt = elements[0].text
        return True, txt
    else:
        return False, ""


def main(url, css, headless):
    logger.info("Starting Firefox")
    current_driver = start_firefox(headless)
    successive_failures = 0
    try:
        while True:
            try:
                success, text = retrieve_text_from_page(
                    driver=current_driver, url=url, page_element_css_id=css
                )
            except Exception:
                # The specific exception is caught by loguru,
                # and saved to the log file
                success,text = False,""
                logger.error(f"Error with url: '{url}'")
            if success:
                logger.info(f"Retrieved headline '{text}'")
                successive_failures = 0
            else:
                successive_failures += 1
                logger.info(f"Failure no {successive_failures}")
                logger.warning(f"Could not retrieve element")
                if successive_failures == 5:
                    logger.warning(f"Tried 5 times. Giving up.")
                    sys.exit(1)
            time.sleep(2)
    except KeyboardInterrupt:
        pass
    finally:
        current_driver.quit()


if __name__ == "__main__":
    arguments = docopt(__doc__, version="linkchecker 0.1")
    ## logging
    logging_directory = Path("/var/log/scraper")
    if logging_directory.exists() and logging_directory.is_dir():
        logger.add(
            Path.joinpath(logging_directory, "scraper.error.log"),
            rotation="1 week",
            retention="6 week",
            level="ERROR",
        )
        logger.add(
            Path.joinpath(logging_directory, "scraper.info.log"),
            rotation="1 week",
            retention="2 week",
            level="INFO",
        )
    #reading config file
    config_path = arguments["--config"]
    if not (Path(config_path).exists() and Path(config_path).is_file()):
        logger.critical(f"Could not find config file '{config_path}'. Quitting.")
        sys.exit(1)
    else:
        configs = configparser.ConfigParser()
        configs.read(config_path)
    URL = configs["css"]["url"]
    CSS_ID = configs["css"]["id"]
    #running main loop
    main(URL, CSS_ID, arguments["--headless"])