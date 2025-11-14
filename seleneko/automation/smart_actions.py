import time
from typing import Optional, Tuple
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    ElementNotInteractableException,
    StaleElementReferenceException,
    WebDriverException,
)


class SmartActionsMixin:
    """
    SeleniumClient に追加される堅牢操作メソッド群。
    クリック・入力・URL変化などを人間的に扱う。
    """

    def click_smart(self, locator: Tuple[str, str], timeout: Optional[int] = None, retries: int = 3,
                    success: Optional[dict] = None, delay: float = 0.3) -> bool:
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
                    try:
                        from selenium.webdriver import ActionChains
                        ActionChains(self.driver).move_to_element(elem).click().perform()
                    except Exception:
                        # Fallback when ActionChains is unavailable (e.g. fake drivers in tests)
                        elem.click()

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
