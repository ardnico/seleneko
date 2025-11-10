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

from .._config import config as _config  # 既存の conf をそのまま使う

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

# ===== 使用例 =====
# with SeleniumClient(DriverSettings(browser="chrome", headless=True)) as cli:
#     cli.get("https://example.com")
#     title = cli.driver.title
#     cli.save_html(os.path.join(cli.conf.get_data("work_directory"), "page.html"))
#     # ログイン例:
#     # cli.login(
#     #     url="https://example.com/login",
#     #     user_locator=("id", "username"),
#     #     pass_locator=("id", "password"),
#     #     button_locator=("css", "button[type=submit]"),
#     #     userid="YOUR_ID",
#     #     password="YOUR_PASS",
#     # )
