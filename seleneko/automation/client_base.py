import os
from typing import Optional, Tuple, Union
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from ..core import config as _config
from .driver_factory import DriverSettings, create_driver, cleanup_tmpdir


class SeleniumClient:
    conf = _config(name=__name__)

    _METHOD_MAP = {
        "id": By.ID, "name": By.NAME, "class": By.CLASS_NAME,
        "css": By.CSS_SELECTOR, "xpath": By.XPATH,
        "tag": By.TAG_NAME, "link_text": By.LINK_TEXT,
        "partial_link_text": By.PARTIAL_LINK_TEXT,
    }

    def __init__(self, settings: Optional[DriverSettings] = None, **kwargs):
        self.settings = settings or DriverSettings()
        self.conf.set_data("browser", self.settings.browser)
        work_directory = kwargs.get("work_directory") or os.path.join(os.getcwd(), self.conf.get_date_str_ymd())
        os.makedirs(work_directory, exist_ok=True)
        self.conf.set_data("work_directory", work_directory)
        self._driver = None
        self._tmpdir = None

    def __enter__(self):
        self._driver, self._tmpdir = create_driver(self.settings, self.conf)
        return self

    def __exit__(self, exc_type, exc, tb):
        self.quit()

    @property
    def driver(self):
        if self._driver is None:
            self._driver, self._tmpdir = create_driver(self.settings, self.conf)
        return self._driver

    def quit(self):
        try:
            if self._driver:
                self._driver.quit()
        finally:
            cleanup_tmpdir(self._tmpdir)
            self._driver = None
            self._tmpdir = None

    # ---- element ops ----
    def find_visible(self, key: str, method="xpath", timeout=None):
        by = self._METHOD_MAP.get(method.lower())
        wait = WebDriverWait(self.driver, timeout or self.settings.timeout_sec)
        return wait.until(EC.visibility_of_element_located((by, key)))

    def click(self, key: str, method="xpath", timeout=None):
        by = self._METHOD_MAP.get(method.lower())
        elem = WebDriverWait(self.driver, timeout or self.settings.timeout_sec).until(EC.element_to_be_clickable((by, key)))
        elem.click()
        return elem

    def type_text(self, key: str, text: str, method="xpath", clear_first=True, enter=False):
        elem = self.find_visible(key, method)
        if clear_first:
            try: elem.clear()
            except Exception: pass
        elem.send_keys(text)
        if enter:
            elem.send_keys(Keys.ENTER)
        return elem

    def select_by_text(self, key: str, visible_text: str, method="xpath"):
        elem = self.find_visible(key, method)
        Select(elem).select_by_visible_text(visible_text)
        return elem

    def select_by_index(self, key: str, index: int, method="xpath"):
        elem = self.find_visible(key, method)
        Select(elem).select_by_index(index)
        return elem

    def switch_to_frame(self, key: Union[str, int] = 0, method="xpath"):
        self.driver.switch_to.default_content()
        if isinstance(key, int):
            self.driver.switch_to.frame(key)
        else:
            frame_elem = self.find_visible(key, method)
            self.driver.switch_to.frame(frame_elem)

    def switch_to_window_by_title(self, title: str, timeout=None):
        wait = WebDriverWait(self.driver, timeout or self.settings.timeout_sec)
        wait.until(lambda d: any(self._switch_if_title(d, h, title) for h in d.window_handles))

    @staticmethod
    def _switch_if_title(driver, handle, title) -> bool:
        driver.switch_to.window(handle)
        return driver.title == title

    # ---- navigation ----
    def get(self, url: str):
        self.driver.get(url)
        WebDriverWait(self.driver, 6).until(
            lambda d: d.execute_script("return document.readyState") in ("interactive", "complete")
        )

    def login(self, url: str, user_locator: Tuple[str, str],
              pass_locator: Tuple[str, str], button_locator: Tuple[str, str],
              userid: str, password: str):
        self.get(url)
        self.type_text(user_locator[1], userid, method=user_locator[0])
        self.type_text(pass_locator[1], password, method=pass_locator[0])
        self.click(button_locator[1], method=button_locator[0])
