import pytest
from selenium.webdriver.common.by import By


class FakeElement:
    """最小限のモック要素。クリックやsend_keysを模倣。"""
    def __init__(self, attrs=None, on_click=None):
        self.attrs = attrs or {}
        self.on_click = on_click or (lambda: None)
        self._cleared = False
        self.sent_keys = []
        self.clicked = False

    def click(self):
        self.clicked = True
        self.on_click()

    def clear(self):
        self._cleared = True
        self.attrs["value"] = ""

    def send_keys(self, value):
        if value == "\ue007":  # Keys.ENTER
            self.attrs["enter"] = True
        else:
            self.attrs["value"] = self.attrs.get("value", "") + str(value)
        self.sent_keys.append(value)

    def get_attribute(self, key):
        return self.attrs.get(key)


class FakeDriver:
    """Selenium WebDriver 互換の軽量モック"""
    def __init__(self):
        self.elements = {}
        self.current_url = "https://example.com/login"
        self.title = "Mock Page"
        self.window_handles = ["main"]

    def add_element(self, by, key, element: FakeElement):
        self.elements[(by, key)] = element

    def find_element(self, by, key):
        if (by, key) not in self.elements:
            raise Exception(f"No such element: {(by, key)}")
        return self.elements[(by, key)]

    def execute_script(self, script, *args):
        # DOM状態などを模倣
        if "document.readyState" in script:
            return "complete"
        return 0

    def get(self, url):
        self.current_url = url

    def switch_to(self):
        return self

    def frame(self, *args, **kwargs): ...
    def default_content(self): ...
    def window(self, *args, **kwargs): ...


@pytest.fixture
def fake_driver(monkeypatch):
    """全テストで使えるモックdriver。"""
    driver = FakeDriver()

    # SeleniumClient.driver を差し替え
    from seleneko.automation import SeleniumClient
    cli = SeleniumClient()
    cli._driver = driver
    cli.driver = driver
    return driver
