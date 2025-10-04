from usesel import Usesel

def main():
    size=(1200,1200)
    usal = Usesel()
    url = "https://www.selenium.dev/ja/documentation/"
    abe_hiroshi_url = "http://abehiroshi.la.coocan.jp/"
    driver = usal.call_driver(size=size)
    driver.get(url)
    driver.switch_to.new_window('tab')
    driver.get(abe_hiroshi_url)
    driver.current_window_handle
    frame_xpath = "/html/frameset/frame[1]"
    usal.moveflame(
        driver = driver,
        key=frame_xpath,
    )
    path = r"/html/body/table/tbody/tr[8]/td[3]/p/a"
    item = usal.get_web_element(driver=driver,key=path,action="click")
    usal.screenshot(
        driver = driver,
        size = size,
        name = 'ScreenShot',  #  name of screenshot
        expa = '.png',  #  extention
        digits = 5,
    )
    usal.printhtml(
        driver = driver,
        file_name = 'prit_test'  #  fille name
    )
    driver.switch_to.new_window('window')
    driver.get(url)
    keys = [
        "/html/body/div/div[1]/div/main/div/div[2]/div[2]/h5/a",
        '//*[@id="docsearch-1"]/button/span[1]/span',
        '//*[@id="docsearch-input"]',
    ]
    actions = [
        "click",
        "click",
        'sendkeys:web',
    ]
    usal.action_web_element(
        driver = driver,
        keys = keys,
        methods = [],
        nums = [3,4,50],
        waittimes = [5,20,1,3],
        actions = actions,
        error_ignore = False,
    )
    waiting = input("")
    driver.quit()

if __name__=="__main__":
    main()