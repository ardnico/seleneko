import os
import shutil
import tempfile
import time
from dataclasses import dataclass
from typing import Optional, Tuple, Union

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    ElementNotInteractableException,
    StaleElementReferenceException,
    TimeoutException,
    WebDriverException,
)

from ..core import config as _config


@dataclass
class DriverSettings:
    browser: str = "chrome"
    window_size: Tuple[int, int] = (700, 700)
    headless: bool = True
    download_dir: Optional[str] = None
    page_load_strategy: str = "eager"
    images_enabled: bool = False
    timeout_sec: int = 15
    tmp_profile: bool = True


class SeleniumClient:
    """
    軽量・堅牢な Selenium クライアント。
    明示 Wait・JS フォールバック・ヘッドレス省メモリ対応。
    """
    conf = _config(name=__name__)

    def __init__(self, settings: Optional[DriverSettings] = None, **kwargs):
        self.settings = settings or DriverSettings()
        self.conf.set_data("browser", self.settings.browser)
        work_directory = kwargs.get("work_directory") or os.path.join(os.getcwd(), self.conf.get_date_str_ymd())
        os.makedirs(work_directory, exist_ok=True)
        self.conf.set_data("work_directory", work_directory)
        self._driver = None
        self._tmpdir = None

    # ---- context manager ----
    def __enter__(self):
        self._driver = self._create_driver()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.quit()

    # ---- property ----
    @property
    def driver(self):
        if self._driver is None:
            self._driver = self._create_driver()
        return self._driver

    def quit(self):
        try:
            if self._driver:
                self._driver.quit()
        finally:
            self._driver = None
            if self._tmpdir and os.path.isdir(self._tmpdir):
                shutil.rmtree(self._tmpdir, ignore_errors=True)
                self._tmpdir = None

    # ---- driver creation ----
    def _create_driver(self):
        browser = (self.settings.browser or "").lower()
        headless = self.settings.headless or browser in ("headless_chrome", "ch")
        download_dir = self.settings.download_dir or self.conf.get_data("work_directory")
        os.makedirs(download_dir, exist_ok=True)

        if browser in ("chrome", "c", "headless_chrome", "ch"):
            options = ChromeOptions()
            self._apply_chrome_flags(options, headless)
            prefs = {"download.default_directory": download_dir, "profile.managed_default_content_settings.images": 2}
            options.add_experimental_option("prefs", prefs)
            if self.settings.tmp_profile:
                self._tmpdir = tempfile.mkdtemp(prefix="selenium-profile-")
                options.add_argument(f"--user-data-dir={self._tmpdir}")
            driver = webdriver.Chrome(service=ChromeService(), options=options)

        elif browser in ("firefox", "ff", "fox"):
            options = FirefoxOptions()
            if headless:
                options.add_argument("-headless")
            driver = webdriver.Firefox(service=FirefoxService(), options=options)

        elif browser in ("edge", "e"):
            options = EdgeOptions()
            self._apply_chrome_flags(options, headless)
            if self.settings.tmp_profile:
                self._tmpdir = tempfile.mkdtemp(prefix="selenium-profile-")
                options.add_argument(f"--user-data-dir={self._tmpdir}")
            driver = webdriver.Edge(service=EdgeService(), options=options)
        else:
            raise ValueError(f"Unsupported browser: {browser}")

        driver.set_page_load_timeout(max(self.settings.timeout_sec, 5))
        driver.set_script_timeout(max(self.settings.timeout_sec, 5))
        driver.set_window_position(0, 0)
        w, h = self.settings.window_size
        driver.set_window_size(w, h)
        return driver

    def _apply_chrome_flags(self, options, headless: bool):
        if headless:
            options.add_argument("--headless=new")
        for arg in [
            "--disable-gpu", "--no-sandbox", "--disable-dev-shm-usage",
            "--disable-extensions", "--mute-audio", "--disable-notifications",
            "--disable-infobars", "--log-level=3", "--ignore-certificate-errors"
        ]:
            options.add_argument(arg)

    # ---- find utilities ----
    _METHOD_MAP = {
        "id": By.ID, "name": By.NAME, "class": By.CLASS_NAME, "css": By.CSS_SELECTOR,
        "xpath": By.XPATH, "tag": By.TAG_NAME, "link_text": By.LINK_TEXT,
        "partial_link_text": By.PARTIAL_LINK_TEXT,
    }

    def find_visible(self, key, method="xpath", timeout=None):
        by = self._METHOD_MAP.get(method.lower())
        wait = WebDriverWait(self.driver, timeout or self.settings.timeout_sec)
        return wait.until(EC.visibility_of_element_located((by, key)))

    # ---- core actions ----
    def get(self, url: str):
        self.driver.get(url)
        WebDriverWait(self.driver, 6).until(
            lambda d: d.execute_script("return document.readyState") in ("interactive", "complete")
        )

    def click(self, key, method="xpath"):
        by = self._METHOD_MAP.get(method.lower())
        elem = WebDriverWait(self.driver, self.settings.timeout_sec).until(EC.element_to_be_clickable((by, key)))
        elem.click()
        return elem

    def type_text(self, key, text, method="xpath", clear_first=True, enter=False):
        elem = self.find_visible(key, method)
        if clear_first:
            try: elem.clear()
            except Exception: pass
        elem.send_keys(text)
        if enter:
            elem.send_keys(Keys.ENTER)
        return elem

    # =====================================================================
    # ここからテストで使われる高信頼メソッド群
    # =====================================================================

    def click_smart(self, locator: Tuple[str, str], timeout: Optional[int] = None, retries: int = 3,
                    success: Optional[dict] = None, delay: float = 0.2) -> bool:
        method, key = locator
        by = self._METHOD_MAP.get(method.lower())
        for attempt in range(retries):
            try:
                elem = WebDriverWait(self.driver, timeout or self.settings.timeout_sec).until(
                    EC.element_to_be_clickable((by, key))
                )
                self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", elem)
                time.sleep(delay)
                try:
                    elem.click()
                except (ElementClickInterceptedException, ElementNotInteractableException):
                    from selenium.webdriver import ActionChains
                    ActionChains(self.driver).move_to_element(elem).click().perform()
                if success:
                    cond = success["callable"]
                    WebDriverWait(self.driver, success.get("timeout", 5)).until(cond)
                return True
            except (StaleElementReferenceException, WebDriverException):
                time.sleep(delay)
        return False

    def type_text_smart(self, locator: Tuple[str, str], text: str,
                        press_enter=False, clear_first=True) -> bool:
        method, key = locator
        try:
            elem = self.find_visible(key, method)
            if clear_first:
                try: elem.clear()
                except Exception: pass
            elem.send_keys(text)
            if press_enter:
                elem.send_keys(Keys.ENTER)
            val = elem.get_attribute("value") or ""
            if text in val:
                return True
            # JS fallback
            self.driver.execute_script("arguments[0].value = arguments[1];", elem, text)
            if press_enter:
                elem.send_keys(Keys.ENTER)
            return True
        except Exception:
            return False

    # ---- expect helpers ----
    def expect_url_change(self, from_url: str, timeout: int = 5):
        def _cond(driver):
            return driver.current_url != from_url
        return {"callable": _cond, "timeout": timeout}

    def expect_appears(self, locator: Tuple[str, str], timeout: int = 5):
        method, key = locator
        by = self._METHOD_MAP.get(method.lower())
        def _cond(driver):
            try:
                driver.find_element(by, key)
                return True
            except Exception:
                return False
        return {"callable": _cond, "timeout": timeout}

    def expect_disappears(self, locator: Tuple[str, str], timeout: int = 5):
        method, key = locator
        by = self._METHOD_MAP.get(method.lower())
        def _cond(driver):
            try:
                driver.find_element(by, key)
                return False
            except Exception:
                return True
        return {"callable": _cond, "timeout": timeout}

    # ---- login ----
    def login(self, url: str, user_locator: Tuple[str, str], pass_locator: Tuple[str, str],
              button_locator: Tuple[str, str], userid: str, password: str,
              url_access=True, success_after=None):
        if url_access:
            self.get(url)
        self.type_text_smart(user_locator, userid)
        self.type_text_smart(pass_locator, password)
        self.click_smart(button_locator, success=success_after)
