from selenium.webdriver.common.by import By
from selenium.common.exceptions import ElementClickInterceptedException
from seleneko.automation import SeleniumClient


def make_client(fake_driver):
    cli = SeleniumClient()
    cli._driver = fake_driver
    cli.driver = fake_driver
    return cli


def test_click_smart_changes_url(fake_driver):
    """click_smart が成功し、URLが変化するかを確認"""
    clicked = {"done": False}

    def on_click():
        clicked["done"] = True
        fake_driver.current_url = "https://example.com/dashboard"

    from seleneko.tests.conftest import FakeElement
    elem = FakeElement(on_click=on_click)
    fake_driver.add_element(By.CSS_SELECTOR, "button[type=submit]", elem)

    cli = make_client(fake_driver)
    before = fake_driver.current_url
    ok = cli.click_smart(("css", "button[type=submit]"),
                         success=cli.expect_url_change(from_url=before))
    assert ok
    assert clicked["done"]
    assert fake_driver.current_url != before


def test_click_smart_fallbacks(fake_driver, monkeypatch):
    """通常クリック→ActionChains fallback動作を確認"""
    from seleneko.tests.conftest import FakeElement
    state = {"count": 0}

    def on_click():
        state["count"] += 1

    elem = FakeElement(on_click=on_click)
    fake_driver.add_element(By.CSS_SELECTOR, "#btn", elem)

    cli = make_client(fake_driver)

    calls = {"n": 0}
    def flaky_click():
        calls["n"] += 1
        if calls["n"] == 1:
            raise ElementClickInterceptedException("blocked")
        else:
            on_click()

    elem.click = flaky_click

    ok = cli.click_smart(("css", "#btn"))
    assert ok
    assert state["count"] == 1


def test_type_text_smart_sets_value(fake_driver):
    """type_text_smart が確実に値を設定できるか"""
    from seleneko.tests.conftest import FakeElement
    input_el = FakeElement(attrs={"value": ""})
    fake_driver.add_element(By.ID, "username", input_el)

    cli = make_client(fake_driver)
    ok = cli.type_text_smart(("id", "username"), "niko", press_enter=True)
    assert ok
    assert input_el.get_attribute("value") == "niko"


def test_expect_helpers(fake_driver):
    """expect_appears/disappears/url_change の基本検証"""
    cli = make_client(fake_driver)
    from seleneko.tests.conftest import FakeElement
    el = FakeElement()
    fake_driver.add_element(By.CSS_SELECTOR, "#ready", el)
    cond = cli.expect_appears(("css", "#ready"))
    assert cond["callable"](fake_driver)
    fake_driver.elements.clear()
    cond2 = cli.expect_disappears(("css", "#ready"))
    assert cond2["callable"](fake_driver)


def test_login_flow(fake_driver):
    """login シーケンス全体の流れを検証"""
    from seleneko.tests.conftest import FakeElement
    user_el = FakeElement(attrs={"value": ""})
    pass_el = FakeElement(attrs={"value": ""})

    def on_submit():
        fake_driver.current_url = "https://example.com/home"

    btn_el = FakeElement(on_click=on_submit)

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
    )
    assert fake_driver.current_url.endswith("/home")
