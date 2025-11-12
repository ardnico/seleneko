import os
import tempfile
import shutil
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.edge.service import Service as EdgeService
from ..core import config as _config


class DriverSettings:
    def __init__(
        self,
        browser="chrome",
        window_size=(800, 800),
        headless=True,
        images_enabled=False,
        download_dir=None,
        tmp_profile=True,
        timeout_sec=15,
        page_load_strategy="eager",
    ):
        self.browser = browser
        self.window_size = window_size
        self.headless = headless
        self.images_enabled = images_enabled
        self.download_dir = download_dir
        self.tmp_profile = tmp_profile
        self.timeout_sec = timeout_sec
        self.page_load_strategy = page_load_strategy


def create_driver(settings: DriverSettings, conf: _config):
    """ブラウザ設定に応じて最適なwebdriverを構築する。"""
    browser = settings.browser.lower()
    headless = settings.headless or browser in ("headless_chrome", "ch")
    download_dir = settings.download_dir or conf.get_data("work_directory")
    os.makedirs(download_dir, exist_ok=True)

    tmpdir = None
    driver = None

    if browser in ("chrome", "c", "headless_chrome", "ch"):
        options = ChromeOptions()
        _apply_common_chrome_flags(options, headless, settings.images_enabled)
        prefs = {
            "download.default_directory": download_dir,
            "download.prompt_for_download": False,
            "profile.managed_default_content_settings.images": 2 if not settings.images_enabled else 1,
        }
        options.add_experimental_option("prefs", prefs)
        if settings.tmp_profile:
            tmpdir = tempfile.mkdtemp(prefix="selenium-profile-")
            options.add_argument(f"--user-data-dir={tmpdir}")
        driver = webdriver.Chrome(service=ChromeService(), options=options)

    elif browser in ("firefox", "ff", "fox"):
        options = FirefoxOptions()
        if headless:
            options.add_argument("-headless")
        options.page_load_strategy = settings.page_load_strategy
        driver = webdriver.Firefox(service=FirefoxService(), options=options)

    elif browser in ("edge", "e"):
        options = EdgeOptions()
        _apply_common_chrome_flags(options, headless, settings.images_enabled)
        if settings.tmp_profile:
            tmpdir = tempfile.mkdtemp(prefix="selenium-profile-")
            options.add_argument(f"--user-data-dir={tmpdir}")
        driver = webdriver.Edge(service=EdgeService(), options=options)

    else:
        raise ValueError(f"Unsupported browser: {browser}")

    driver.set_page_load_timeout(max(settings.timeout_sec, 5))
    driver.set_script_timeout(max(settings.timeout_sec, 5))
    driver.set_window_position(0, 0)
    w, h = settings.window_size
    driver.set_window_size(w, h)
    return driver, tmpdir


def _apply_common_chrome_flags(options, headless: bool, images_enabled: bool):
    if headless:
        options.add_argument("--headless=new")
    for arg in [
        "--disable-gpu", "--no-sandbox", "--disable-dev-shm-usage",
        "--disable-extensions", "--mute-audio", "--disable-notifications",
        "--disable-infobars", "--log-level=3", "--ignore-certificate-errors",
    ]:
        options.add_argument(arg)
    if not images_enabled:
        options.add_argument("--blink-settings=imagesEnabled=false")


def cleanup_tmpdir(tmpdir: str):
    if tmpdir and os.path.isdir(tmpdir):
        shutil.rmtree(tmpdir, ignore_errors=True)
