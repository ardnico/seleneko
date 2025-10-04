
import os
import glob
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from .._config import config

class use_selenium(object):
    conf = config(name=__name__)
    def __init__(
        self,
        browser="chrome",
        work_directory=None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.conf.set_data("browser",browser)
        if work_directory is None:
            work_directory = os.path.join(os.getcwd(),self.conf.get_date_str_ymd())
        self.conf.set_data("work_directory",work_directory)
    
    def call_driver(
        self,
        size=(700,700),
        **kwargs
    ):
        """_summary_
        Args:
            size (tuple, optional): browser size. Defaults to (700,700).
        """
        self.conf.set_log()
        options = Options()
        browser_type = self.conf.get_data("browser")
        if browser_type in ["chrome","c"]:
            # Google Chrome
            driver = webdriver.Chrome(**kwargs)
        elif browser_type in ["headless_chrome","ch"]:
            # Google (HeadlessMode)
            options.add_argument('--headless')
            options.add_argument('--allow-insecure-localhost')
            options.add_argument('--ignore-certificate-errors')
            driver = webdriver.Chrome(options=options, **kwargs)
        elif browser_type in ["firefox","ff","fox"]:
            # firefox
            fp = webdriver.FirefoxProfile()
            fp.set_preference("browser.download.dir", self.conf.get_data("work_directory"))
            driver = webdriver.Firefox(firefox_profile=fp, **kwargs)
        elif browser_type in ["edge","e"]:
            # Edge
            driver = webdriver.Edge(**kwargs)
        elif browser_type in ["ie"]:
            # IE
            self.conf.write_log("InternetExplorer's service is expired",species="INFO")
            return None
        else:
            self.conf.write_log("Not Conpatible browser: " + self.conf.get_data('browser') ,species="INFO")
            return None
        driver.set_window_position(0,0)
        driver.set_window_size(size[0],size[1])
        return driver
    
    @conf.log_exception
    def get_web_element(
        self,
        driver = None,
        key = '',  # Search keyword
        method = 'xpath',  # search method
        num = 3,  # try count
        waittime = 2,
        action = "",
    ):
        if driver is None:
            self.conf.write_log(f"driver is not selected",species="ERROR")
            raise Exception
        reitem = None
        method_dic = {
            "class"                 : By.CLASS_NAME
            ,"class_name"           : By.CLASS_NAME
            ,"classname"            : By.CLASS_NAME
            ,"cn"                   : By.CLASS_NAME
            ,"id"                   : By.ID
            ,"name"                 : By.NAME
            ,"link_text"            : By.LINK_TEXT
            ,"linktext"             : By.LINK_TEXT
            ,"link"                 : By.LINK_TEXT
            ,"lt"                   : By.LINK_TEXT
            ,"partial_link_text"    : By.PARTIAL_LINK_TEXT
            ,"partiallink_text"     : By.PARTIAL_LINK_TEXT
            ,"partial_linktext"     : By.PARTIAL_LINK_TEXT
            ,"partiallinktext"      : By.PARTIAL_LINK_TEXT
            ,"tag_name"             : By.TAG_NAME
            ,"tagname"              : By.TAG_NAME
            ,"tag"                  : By.TAG_NAME
            ,"xpath"                : By.XPATH
            ,"x"                    : By.XPATH
            ,"css_selector"         : By.CSS_SELECTOR
            ,"cssselector"          : By.CSS_SELECTOR
            ,"css"                  : By.CSS_SELECTOR
            ,"cs"                   : By.CSS_SELECTOR
        }
        for _ in range(num):
            try:
                if method in method_dic.keys():
                    reitem = driver.find_element(method_dic[method],key)
                    if action:
                        self.done_action(element=reitem,action=action)
                    return reitem
                else:
                    self.conf.write_log("no such elements",species="ERROR")
                    raise Exception
            except Exception as e:
                time.sleep(waittime)
                self.conf.write_log(f"error info {str(e)}",species="DEBUG")
                self.conf.write_log(f"retry to get a web element: {key}\nmethod:{method}",species="DEBUG")
        self.conf.write_log(f"failed to get a web element: {key}\nmethod:{method}",species="ERROR")
        raise Exception
    
    @conf.log_exception
    def done_action(
            self,
            element,
            action,
        ):
        if action=="click":
            element.click()
        elif action=="clear":
            element.clear()
        elif action.find('send_keys')==0 or action.find('sendkeys')==0:
            keyword = action[action.find(":")+1:]
            element.send_keys(keyword)
        elif action.find('enter')==0:
            element.send_keys(Keys.ENTER)
        elif action.find('select_by_index')==0:
            keyword = action[action.find(":")+1:]
            element.select_by_index(keyword)
        elif action.find('select_by_visible_text')==0:
            keyword = action[action.find(":")+1:]
            element.select_by_visible_text(keyword)
        elif action=='deselect_all':
            element.deselect_all()
        elif action.find('deselect_by_index')==0:
            keyword = action[action.find(":")+1:]
            element.deselect_by_index(keyword)
        elif action.find('deselect_by_value')==0:
            keyword = action[action.find(":")+1:]
            element.deselect_by_value(keyword)
        elif action.find('deselect_by_visible_text')==0:
            keyword = action[action.find(":")+1:]
            element.deselect_by_visible_text(keyword)
        elif action.find('click_and_hold')==0:
            keyword = action[action.find(":")+1:]
            element.click_and_hold(keyword)
        elif action.find('move_to_element')==0:
            keyword = action[action.find(":")+1:]
            element.move_to_element(keyword)
        elif action=='key_down' or action=='down':
            element.key_down('key_down')
        elif action=='key_up' or action=='up':
            element.key_down('key_up')
        else:
            self.conf.write_log(f"unknown action {action}",species="ERROR")
    
    @conf.log_exception
    def action_web_element(
        self,
        driver = None,
        keys = [],
        methods = ["xpath"],
        nums = [3],
        waittimes = [2],
        actions = [
            f"send_keys:{id}",
            f"send_keys:{psw}",
            "click",
            ""
        ]
        
        for i, key in enumerate(keys):
            num = nums[i] if len(nums) > i else 3
            waittime = waittimes[i] if len(waittimes) > i else 2
            method = methods[i] if len(methods) > i else "xpath"
            try:
                self.get_web_element(
                driver = driver,
                key = key,
                method = method,
                num = num,
                waittime = waittime,
                action = actions[i],
                )
            except Exception as e:
                self.conf.write_log(f"error occured: {str(e)}",species="ERROR")
                if error_ignore==False:
                    raise Exception
    
    @conf.log_exception
    def moveflame(
        self,
        driver = None,
        key="",
        method="xpath",
        **args
    ):
        flame_item = self.get_web_element(driver = driver,key=key,method=method,**args)
        try:
            driver.switch_to.default_content()
        except:
            pass
        driver.switch_to.frame(flame_item)
    
    @conf.log_exception
    def login(
        self,
        driver,
        url,
        paths:list, # specify the xpath(idbox,passwordbox,button,check)
        method="xpath",
        **kwargs
    ):
        if len(paths)!=4:
            waiting = input("specify the xpath(idbox,passwordbox,button,check)")
            raise Exception
        id, psw = self.conf.get_id()
        actions = [
            f"send_keys:{id}",
            f"send_keys:{psw}",
            if action=="click":
                element.click()
            elif action=="clear":
                element.clear()
            elif action.find('send_keys')==0 or action.find('sendkeys')==0:
                keyword = action[action.find(":")+1:]
                element.send_keys(keyword)
            elif action.find('enter')==0:
                element.send_keys(Keys.ENTER)
            elif action.find('select_by_index')==0:
                keyword = action[action.find(":")+1:]
                element.select_by_index(keyword)
            elif action.find('select_by_visible_text')==0:
                keyword = action[action.find(":")+1:]
                element.select_by_visible_text(keyword)
            elif action=='deselect_all':
                element.deselect_all()
            elif action.find('deselect_by_index')==0:
                keyword = action[action.find(":")+1:]
                element.deselect_by_index(keyword)
            elif action.find('deselect_by_value')==0:
                keyword = action[action.find(":")+1:]
                element.deselect_by_value(keyword)
            elif action.find('deselect_by_visible_text')==0:
                keyword = action[action.find(":")+1:]
                element.deselect_by_visible_text(keyword)
            elif action.find('click_and_hold')==0:
                keyword = action[action.find(":")+1:]
                element.click_and_hold(keyword)
            elif action.find('move_to_element')==0:
                keyword = action[action.find(":")+1:]
                element.move_to_element(keyword)
            elif action=='key_down' or action=='down':
                element.send_keys(Keys.DOWN)
            elif action=='key_up' or action=='up':
                element.send_keys(Keys.UP)
            else:
                self.conf.write_log(f"unknown action {action}",species="ERROR")
    def printhtml(
        self,
        driver = None,
        file_name = 'print'  #  fille name
    ):
        '''
        write as html file
        '''
        path = f'{file_name}.html'
        with open(path, mode='w', encoding="utf-8") as f:
            f.write(driver.page_source)
        return
    
    @conf.log_exception
    def get_handle(
        self,
        driver = None,
        name = "", # title
    ):
        '''
        '''
                elif action=='key_down' or action=='down':
                    element.send_keys(Keys.DOWN)
                elif action=='key_up' or action=='up':
                    element.send_keys(Keys.UP)
                driver.switch_to.window(driver.window_handles[-1])
                return
        
        if driver.title == name:
            return

        for handle in driver.window_handles:
                driver.switch_to.window(handle)
                if driver.title == name:
                    return
        