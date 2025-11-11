import os
import shutil
import tempfile
from dataclasses import dataclass
from typing import Optional, Tuple, Iterable, Union

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

from ..core import config as _config  # 既存の conf をそのまま使う

# ====== 設定データ ======
@dataclass
class DriverSettings:
    browser: str = "chrome"                      # "chrome" | "firefox" | "edge" | "headless_chrome"
    window_size: Tuple[int, int] = (700, 700)
    headless: bool = True
    download_dir: Optional[str] = None
    page_load_strategy: str = "eager"            # "none" | "eager" | "normal"
    images_enabled: bool = False                 # メモリ節約のため既定でオフ
    timeout_sec: int = 15                        # 明示Waitの既定
    tmp_profile: bool = True                     # 使い捨てプロファイルでリーク抑制

# ====== 主要クラス ======
class SeleniumClient:
    """
    省メモリ・高安定を狙った Selenium の薄いラッパ。
    - コンテキストマネージャ対応で quit 漏れ防止
    - 明示 Wait / 軽量オプション / 一時プロファイル
    - 汎用ユーティリティ（要素取得・入力・クリック・フレーム/ウィンドウ切替）
    """
    conf = _config(name=__name__)

    def __init__(self, settings: Optional[DriverSettings] = None, **kwargs):
        self.settings = settings or DriverSettings()
        # 互換: 既存コードが browser/work_directory を conf に書く前提を維持
        self.conf.set_data("browser", self.settings.browser)
        work_directory = kwargs.get("work_directory") or os.path.join(os.getcwd(), self.conf.get_date_str_ymd())
        os.makedirs(work_directory, exist_ok=True)
        self.conf.set_data("work_directory", work_directory)

        self._driver = None
        self._tmpdir = None  # user-data-dir 用

    # ---- Context Manager ----
    def __enter__(self):
        self._driver = self._create_driver()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.quit()

    # ---- Public API ----
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
            # 一時プロファイルを破棄
            if self._tmpdir and os.path.isdir(self._tmpdir):
                shutil.rmtree(self._tmpdir, ignore_errors=True)
                self._tmpdir = None

    # ---- Driver creation ----
    def _create_driver(self):
        browser = (self.settings.browser or "").lower()
        headless = self.settings.headless or browser in ("headless_chrome", "ch")
        download_dir = self.settings.download_dir or self.conf.get_data("work_directory")
        os.makedirs(download_dir, exist_ok=True)

        page_load_strategy = self.settings.page_load_strategy

        if browser in ("chrome", "c", "headless_chrome", "ch"):
            options = ChromeOptions()
            self._apply_common_chrome_flags(options, headless, images_enabled=self.settings.images_enabled)
            options.page_load_strategy = page_load_strategy
            # ダウンロード抑制 & ディレクトリ固定
            prefs = {
                "download.default_directory": download_dir,
                "download.prompt_for_download": False,
                "profile.default_content_setting_values.automatic_downloads": 1,
            }
            if not self.settings.images_enabled:
                # 画像無効化（blink-settings が効かないケースの保険）
                prefs["profile.managed_default_content_settings.images"] = 2
            options.add_experimental_option("prefs", prefs)

            if self.settings.tmp_profile:
                self._tmpdir = tempfile.mkdtemp(prefix="selenium-profile-")
                options.add_argument(f"--user-data-dir={self._tmpdir}")

            service = ChromeService()  # 既存の chromedriver を PATH で解決する想定（オフライン運用向け）
            driver = webdriver.Chrome(service=service, options=options)

        elif browser in ("firefox", "ff", "fox"):
            options = FirefoxOptions()
            if headless:
                options.add_argument("-headless")
            options.page_load_strategy = page_load_strategy
            # 画像無効は Firefox は about:config を使う（headless では体感差あり）
            # user.js 書き込みを避けるため今回は最小限
            profile_dir = None
            if self.settings.tmp_profile:
                profile_dir = tempfile.mkdtemp(prefix="selenium-profile-")
                self._tmpdir = profile_dir
                options.set_preference("browser.download.dir", download_dir)
                options.set_preference("browser.download.folderList", 2)
                options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/octet-stream")

            service = FirefoxService()
            driver = webdriver.Firefox(service=service, options=options)

        elif browser in ("edge", "e"):
            options = EdgeOptions()
            self._apply_common_edge_flags(options, headless, images_enabled=self.settings.images_enabled)
            options.page_load_strategy = page_load_strategy

            if self.settings.tmp_profile:
                self._tmpdir = tempfile.mkdtemp(prefix="selenium-profile-")
                options.add_argument(f"--user-data-dir={self._tmpdir}")

            service = EdgeService()
            driver = webdriver.Edge(service=service, options=options)

        else:
            self.conf.write_log(f"Not compatible browser: {browser}", species="ERROR")
            raise ValueError(f"Unsupported browser: {browser}")

        # 既定タイムアウト（暗黙 Wait は 0。明示 Wait を使う）
        driver.set_page_load_timeout(max(self.settings.timeout_sec, 5))
        driver.set_script_timeout(max(self.settings.timeout_sec, 5))
        driver.set_window_position(0, 0)
        w, h = self.settings.window_size
        driver.set_window_size(w, h)
        return driver

    # ---- Chrome/Edge flags ----
    def _apply_common_chrome_flags(self, options: ChromeOptions, headless: bool, images_enabled: bool):
        if headless:
            # new の方が描画系プロセスが少なく安定
            options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-extensions")
        options.add_argument("--mute-audio")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-infobars")
        options.add_argument("--window-position=0,0")
        options.add_argument("--log-level=3")
        options.add_argument("--allow-insecure-localhost")
        options.add_argument("--ignore-certificate-errors")
        # 画像停止（効く環境の保険）
        if not images_enabled:
            options.add_argument("--blink-settings=imagesEnabled=false")

    def _apply_common_edge_flags(self, options: EdgeOptions, headless: bool, images_enabled: bool):
        # Edge は Chromium ベース
        if headless:
            options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-extensions")
        options.add_argument("--mute-audio")
        options.add_argument("--disable-notifications")
        if not images_enabled:
            options.add_argument("--blink-settings=imagesEnabled=false")

    # ===== 要素ユーティリティ =====
    _METHOD_MAP = {
        "class": By.CLASS_NAME, "class_name": By.CLASS_NAME, "classname": By.CLASS_NAME, "cn": By.CLASS_NAME,
        "id": By.ID, "name": By.NAME,
        "link_text": By.LINK_TEXT, "linktext": By.LINK_TEXT, "link": By.LINK_TEXT, "lt": By.LINK_TEXT,
        "partial_link_text": By.PARTIAL_LINK_TEXT, "plt": By.PARTIAL_LINK_TEXT,
        "tag_name": By.TAG_NAME, "tag": By.TAG_NAME,
        "xpath": By.XPATH, "x": By.XPATH,
        "css_selector": By.CSS_SELECTOR, "cssselector": By.CSS_SELECTOR, "css": By.CSS_SELECTOR, "cs": By.CSS_SELECTOR,
    }

    def find(self, key: str, method: str = "xpath", timeout: Optional[int] = None):
        """明示 Wait で単一要素を取得。"""
        by = self._METHOD_MAP.get(method.lower())
        if not by:
            raise ValueError(f"Unknown locator method: {method}")
        wait = WebDriverWait(self.driver, timeout or self.settings.timeout_sec)
        return wait.until(EC.presence_of_element_located((by, key)))

    def find_visible(self, key: str, method: str = "xpath", timeout: Optional[int] = None):
        by = self._METHOD_MAP.get(method.lower())
        if not by:
            raise ValueError(f"Unknown locator method: {method}")
        wait = WebDriverWait(self.driver, timeout or self.settings.timeout_sec)
        return wait.until(EC.visibility_of_element_located((by, key)))

    def click(self, key: str, method: str = "xpath", timeout: Optional[int] = None):
        by = self._METHOD_MAP.get(method.lower())
        wait = WebDriverWait(self.driver, timeout or self.settings.timeout_sec)
        elem = wait.until(EC.element_to_be_clickable((by, key)))
        elem.click()
        return elem

    def type_text(self, key: str, text: str, method: str = "xpath", clear_first: bool = True, enter: bool = False):
        elem = self.find_visible(key, method)
        if clear_first:
            try:
                elem.clear()
            except Exception:
                pass
        elem.send_keys(text)
        if enter:
            elem.send_keys(Keys.ENTER)
        return elem

    def select_by_text(self, key: str, visible_text: str, method: str = "xpath"):
        elem = self.find_visible(key, method)
        Select(elem).select_by_visible_text(visible_text)
        return elem

    def select_by_index(self, key: str, index: int, method: str = "xpath"):
        elem = self.find_visible(key, method)
        Select(elem).select_by_index(index)
        return elem

    # ===== フレーム/ウィンドウ =====
    def switch_to_frame(self, key: Union[str, int] = 0, method: str = "xpath"):
        """key が int のときは index、str のときはロケータで切替。"""
        self.driver.switch_to.default_content()
        if isinstance(key, int):
            self.driver.switch_to.frame(key)
        else:
            frame_elem = self.find(key, method)
            self.driver.switch_to.frame(frame_elem)

    def switch_to_window_by_title(self, title: str, timeout: Optional[int] = None):
        wait = WebDriverWait(self.driver, timeout or self.settings.timeout_sec)
        wait.until(lambda d: any(self._switch_if_title(d, h, title) for h in d.window_handles))

    @staticmethod
    def _switch_if_title(driver, handle, title) -> bool:
        driver.switch_to.window(handle)
        return driver.title == title

    # ===== ページ取得系 =====
    def get(self, url: str):
        """eager戦略＋明示Wait前提で高速遷移。"""
        self.driver.get(url)
        # 画面が軽く落ち着くまで短い待機（DOMの初期化を待つ）
        WebDriverWait(self.driver, max(3, min(6, self.settings.timeout_sec))).until(
            lambda d: d.execute_script("return document.readyState") in ("interactive", "complete")
        )

    def save_html(self, path: str):
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.driver.page_source)

    # ===== ログイン・シナリオ例 =====
    def login(self, url: str, user_locator: Tuple[str, str], pass_locator: Tuple[str, str],
              button_locator: Tuple[str, str], userid: str, password: str):
        """
        ログイン共通パターン（余計な retry を廃し、Wait で最短完了）
        locators: (method, key) のタプル
        """
        self.get(url)
        self.type_text(user_locator[1], userid, method=user_locator[0], clear_first=True)
        self.type_text(pass_locator[1], password, method=pass_locator[0], clear_first=True)
        self.click(button_locator[1], method=button_locator[0])


from selenium.common.exceptions import (
    ElementClickInterceptedException,
    StaleElementReferenceException,
    TimeoutException,
    JavascriptException,
)

# ===================== 追加：内部ユーティリティ =====================

def _sleep_short(seconds: float, driver):
    # 極短い安定化待ち（暗黙 wait 0 前提）
    driver.execute_script("return 0")  # イベントループを一度回す
    import time; time.sleep(seconds)

def _exp_backoff(attempt: int, base: float = 0.15, cap: float = 1.2) -> float:
    import math
    return min(cap, base * (2 ** max(0, attempt-1)))


# ===================== 追加：成功条件ビルダ =====================
# 呼び出し時に success=... で渡して使う。
# 例: success=self.expect_url_change(), success=self.expect_appears(("css","#dashboard"))
def expect_url_change(self, from_url: str = None, timeout: Optional[int] = None):
    def cond(driver):
        return (driver.current_url != from_url) if from_url else False
    return {"callable": cond, "timeout": timeout}

def expect_appears(self, locator: Tuple[str, str], timeout: Optional[int] = None):
    method, key = locator
    by = self._METHOD_MAP[method.lower()]
    def cond(driver):
        try:
            return driver.find_element(by, key) is not None
        except Exception:
            return False
    return {"callable": cond, "timeout": timeout}

def expect_disappears(self, locator: Tuple[str, str], timeout: Optional[int] = None):
    method, key = locator
    by = self._METHOD_MAP[method.lower()]
    def cond(driver):
        try:
            driver.find_element(by, key)
            return False
        except Exception:
            return True
    return {"callable": cond, "timeout": timeout}

def expect_value_set(self, locator: Tuple[str, str], expected: str, timeout: Optional[int] = None):
    method, key = locator
    by = self._METHOD_MAP[method.lower()]
    def cond(driver):
        try:
            el = driver.find_element(by, key)
            return (el.get_attribute("value") or "") == expected
        except Exception:
            return False
    return {"callable": cond, "timeout": timeout}


# ===================== 追加：中心点が覆われていないかの判定 =====================
def _is_center_clickable(self, element) -> bool:
    try:
        rect = self.driver.execute_script("""
            const r = arguments[0].getBoundingClientRect();
            return {x: Math.floor(r.left + r.width/2), y: Math.floor(r.top + r.height/2)};
        """, element)
        if rect is None:
            return True  # 取れなければ判定不能→許容
        x, y = rect["x"], rect["y"]
        top_elem = self.driver.execute_script("return document.elementFromPoint(arguments[0], arguments[1]);", x, y)
        if top_elem is None:
            return True
        # クリック対象自身か、その子孫ならOK
        return self.driver.execute_script("""
            let e = arguments[0], t = arguments[1];
            while (t) { if (t === e) return true; t = t.parentElement; }
            return false;
        """, element, top_elem) is True
    except JavascriptException:
        return True


# ===================== 追加：堅牢クリック =====================
def click_smart(self, locator: Tuple[str, str], timeout: Optional[int] = None,
                attempts: int = 4, success: Optional[dict] = None):
    """
    クリックが“効いた”ことまで検証してリトライ。
    - locator: ("css", "#login"), ("xpath", "//button[...]") など
    - success: self.expect_xxx() で作った条件（URL変化、要素出現/消滅、値設定など）
    """
    method, key = locator
    by = self._METHOD_MAP[method.lower()]
    success_callable = success["callable"] if success else None
    success_timeout = success.get("timeout") if success else None
    wait_timeout = timeout or self.settings.timeout_sec

    last_err = None
    for i in range(1, attempts+1):
        try:
            # 要素がクリック可能になるまで待つ
            elem = WebDriverWait(self.driver, wait_timeout).until(EC.element_to_be_clickable((by, key)))
            # スクロールして位置を安定化
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center', inline:'center'});", elem)
            _sleep_short(0.05, self.driver)

            # 覆い被さり検出（ヘッドフルでありがち）
            if not self._is_center_clickable(elem):
                # 微小スクロールで再トライ
                self.driver.execute_script("window.scrollBy(0, -40);")
                _sleep_short(0.06, self.driver)

            # 1) 通常クリック
            try:
                elem.click()
            except (ElementClickInterceptedException, StaleElementReferenceException):
                # 2) Actions クリック
                try:
                    from selenium.webdriver import ActionChains
                    ActionChains(self.driver).move_to_element(elem).pause(0.01).click().perform()
                except Exception:
                    # 3) JS クリック
                    self.driver.execute_script("arguments[0].click();", elem)

            # 成功条件の検証
            if success_callable:
                # 成功待ち（短め、個別指定があればそれを使用）
                ok = WebDriverWait(self.driver, success_timeout or max(2, int(wait_timeout/2))).until(lambda d: success_callable(d))
                if ok:
                    return True
            else:
                # 明示の成功条件がない場合は「短い待機 + 例外なし」を成功とみなす
                _sleep_short(0.08, self.driver)
                return True

        except TimeoutException as e:
            last_err = e
        except Exception as e:
            last_err = e

        # 失敗 → バックオフして再試行
        self.conf.write_log(f"click_smart retry {i}/{attempts} for {locator}: {type(last_err).__name__} {last_err}", species="WARNING")
        _sleep_short(_exp_backoff(i), self.driver)

    # 全滅
    if last_err:
        self.conf.write_log(f"click_smart failed for {locator}: {type(last_err).__name__} {last_err}", species="ERROR")
    raise last_err or TimeoutException(f"click_smart timed out: {locator}")


# ===================== 追加：堅牢入力（検証付き） =====================
def type_text_smart(self, locator: Tuple[str, str], text: str, clear_first: bool = True,
                    press_enter: bool = False, timeout: Optional[int] = None, attempts: int = 3):
    method, key = locator
    by = self._METHOD_MAP[method.lower()]
    wait_timeout = timeout or self.settings.timeout_sec
    last_err = None

    for i in range(1, attempts+1):
        try:
            elem = WebDriverWait(self.driver, wait_timeout).until(EC.visibility_of_element_located((by, key)))
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center', inline:'center'});", elem)
            if clear_first:
                try: elem.clear()
                except Exception: pass
            elem.send_keys(text)
            if press_enter:
                elem.send_keys(Keys.ENTER)

            # 値が入ったか検証
            val = elem.get_attribute("value") or ""
            if val == text or (press_enter and text in val):
                return True
            self.driver.execute_script("arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('input',{bubbles:true}));", elem, text)
            _sleep_short(0.05, self.driver)
            val2 = elem.get_attribute("value") or ""
            if val2 == text:
                if press_enter: elem.send_keys(Keys.ENTER)
                return True

        except Exception as e:
            last_err = e

        self.conf.write_log(f"type_text_smart retry {i}/{attempts} for {locator}: {last_err}", species="WARNING")
        _sleep_short(_exp_backoff(i), self.driver)

    raise last_err or TimeoutException(f"type_text_smart timed out: {locator}")

