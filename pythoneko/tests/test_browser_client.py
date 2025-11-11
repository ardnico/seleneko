import pytest
from unittest.mock import MagicMock
from selenium.webdriver.common.by import By
from selenium.common.exceptions import ElementClickInterceptedException

from seleneko.automation import SeleniumClient, DriverSettings

def make_client(fake_driver):
    # settings は headless True/False どちらでも可（driver はモック化）
    cli = SeleniumClient(DriverSettings(headless=False))
    # 内部ドライバを差し替え
    cli._driver = fake_driver
    return cli

def test_click_smart_changes_url(fake_driver):
    # 準備：クリック対象ボタン
    clicked = {"done": False}
    def on_click():
        clicked["done"] = True
        fake_driver.current_url = "https://example.com/dashboard"

    button = fake_driver.add_element(By.CSS_SELECTOR, "button[type=submit]",
                                     elem := __import__("tests.conftest").conftest.FakeElement(on_click=on_click))

    cli = make_client(fake_driver)
    before = fake_driver.current_url
    ok = cli.click_smart(("css", "button[type=submit]"),
                         success=cli.expect_url_change(from_url=before))
    assert ok is True
    assert clicked["done"] is True
    assert fake_driver.current_url.endswith("/dashboard")

def test_click_smart_fallbacks(fake_driver, monkeypatch):
    # 1回目の click でインターセプト → Actions でも失敗 → JS click で成功…を擬似的に再現
    state = {"count": 0}

    def on_click():
        c = state["count"]
        state["count"] += 1
        if c == 0:
            # 1回目は通常 click で例外を出したいので、FakeElement.click 内では例外を送出できない
            # → monkeypatch で elem.click を差し替えて例外を出す
            pass

    elem = __import__("tests.conftest").conftest.FakeElement(on_click=on_click)
    fake_driver.add_element(By.CSS_SELECTOR, "#btn", elem)

    cli = make_client(fake_driver)

    # elem.click を 1回目だけ例外にする
    calls = {"n": 0}
    def flaky_click():
        calls["n"] += 1
        if calls["n"] == 1:
            raise ElementClickInterceptedException("blocked")
        else:
            on_click()

    elem.click = flaky_click

    ok = cli.click_smart(("css", "#btn"))
    assert ok is True
    assert state["count"] >= 1  # クリックは最終的に通った

def test_type_text_smart_sets_value(fake_driver):
    input_el = __import__("tests.conftest").conftest.FakeElement(attrs={"value": ""})
    fake_driver.add_element(By.ID, "username", input_el)

    cli = make_client(fake_driver)
    assert cli.type_text_smart(("id", "username"), "niko", press_enter=True) is True
    assert input_el.get_attribute("value") == "niko"

def test_expect_helpers(fake_driver):
    cli = make_client(fake_driver)
    # appears: 存在しない → 先に置く
    el = __import__("tests.conftest").conftest.FakeElement()
    fake_driver.add_element(By.CSS_SELECTOR, "#ready", el)
    cond = cli.expect_appears(("css", "#ready"))
    assert cond["callable"](fake_driver) is True

    # disappears
    cond2 = cli.expect_disappears(("css", "#gone"))
    assert cond2["callable"](fake_driver) is True  # そもそも無いので True

def test_login_flow(fake_driver):
    # ユーザー名・パスワード・ボタン
    user_el = __import__("tests.conftest").conftest.FakeElement(attrs={"value": ""})
    pass_el = __import__("tests.conftest").conftest.FakeElement(attrs={"value": ""})
    def on_submit():
        fake_driver.current_url = "https://example.com/home"
    btn_el = __import__("tests.conftest").conftest.FakeElement(on_click=on_submit)

    fake_driver.add_element(By.ID, "user", user_el)
    fake_driver.add_element(By.ID, "pass", pass_el)
    fake_driver.add_element(By.CSS_SELECTOR, "button[type=submit]", btn_el)

    cli = make_client(fake_driver)
    cli.login(
        url="https://example.com/login",
        user_locator=("id", "user"),
        pass_locator=("id", "pass"),
        button_locator=("css", "button[type=submit]"),
        userid="niko",
        password="secret",
        url_access=True,
        success_after=cli.expect_url_change(from_url=fake_driver.current_url),
    )

    assert user_el.get_attribute("value") == "niko"
    assert pass_el.get_attribute("value") == "secret"
    assert fake_driver.current_url.endswith("/home")
