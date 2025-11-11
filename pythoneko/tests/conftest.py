import types
import pytest
from unittest.mock import MagicMock
from selenium.webdriver.common.by import By

# ---- フェイク要素 ----
class FakeElement:
    def __init__(self, tag="div", text="", attrs=None, on_click=None):
        self.tag_name = tag
        self._text = text
        self._attrs = attrs or {}
        self._on_click = on_click or (lambda: None)
        self._cleared = False
        self._value = self._attrs.get("value", "")

    def click(self):
        self._on_click()

    def clear(self):
        self._cleared = True
        self._value = ""

    def send_keys(self, s):
        # ここでは単純に value を連結
        self._value += s

    def get_attribute(self, name):
        if name == "value":
            return self._value
        return self._attrs.get(name)

# ---- フェイク driver.switch_to ----
class _SwitchTo:
    def __init__(self, driver):
        self._driver = driver

    def default_content(self):
        self._driver._frame = None

    def frame(self, f):
        self._driver._frame = f

    def window(self, handle):
        self._driver._current_handle = handle

# ---- フェイク WebDriver ----
class FakeDriver:
    def __init__(self):
        self.current_url = "https://example.com/login"
        self._title = "Example Login"
        self._elems = {}  # (By, key) -> FakeElement
        self._scripts = []
        self._frame = None
        self._current_handle = "main"
        self.window_handles = ["main"]
        self.switch_to = _SwitchTo(self)

    @property
    def title(self):
        return self._title

    def set_title(self, t):
        self._title = t

    def add_element(self, by, key, elem: FakeElement):
        self._elems[(by, key)] = elem

    def find_element(self, by, key):
        if (by, key) not in self._elems:
            raise Exception(f"element not found: {(by, key)}")
        return self._elems[(by, key)]

    def execute_script(self, script, *args):
        # 最低限の振る舞いだけ：readyState, elementFromPoint, click 代替, scroll など
        self._scripts.append(script)
        if "document.readyState" in script:
            return "complete"
        if "elementFromPoint" in script:
            # 擬似的に対象要素自身を返したいが、ここでは「常に対象要素を返した」と見做す
            return args[0] if args else None
        if "arguments[0].click()" in script and args:
            try:
                args[0].click()
            except Exception:
                pass
            return None
        if "scrollIntoView" in script:
            return None
        if "window.scrollBy" in script:
            return None
        if "getBoundingClientRect" in script:
            # 中心座標のダミー
            return {"x": 100, "y": 100}
        if "arguments[0].value =" in script and len(args) >= 2:
            el, value = args[0], args[1]
            el._value = value
            return None
        return None

    def get(self, url):
        self.current_url = url

    def set_page_load_timeout(self, *_):
        pass

    def set_script_timeout(self, *_):
        pass

    def set_window_position(self, *_):
        pass

    def set_window_size(self, *_):
        pass

    def quit(self):
        pass

@pytest.fixture
def fake_driver():
    return FakeDriver()


# ---- WebDriverWait を差し替えるためのヘルパ ----
class ImmediateWait:
    """until(predicate) を即時に評価して返す簡易モック"""
    def __init__(self, driver, timeout=0):
        self._driver = driver
        self._timeout = timeout

    def until(self, predicate):
        # predicate が ExpectedCondition の場合は呼び出し可能
        res = predicate(self._driver)
        # EC の多くは要素や True を返す。False/None は失敗。
        if not res:
            raise AssertionError("Condition not met immediately in ImmediateWait")
        return res

@pytest.fixture(autouse=True)
def patch_wait(monkeypatch):
    from selenium.webdriver.support import ui as ui_mod
    monkeypatch.setattr(ui_mod, "WebDriverWait", ImmediateWait)
    yield
