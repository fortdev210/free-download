import os
import random
import time
from playwright.sync_api import sync_playwright
import settings


class BotManager:
    def __init__(self, **kwargs):
        self.playwright = None
        self.browser = None
        self.page = None
        self._default_page_width = 1800
        self._default_page_height = 800

        # we only run 2 browsers now: firefox + chrome
        self.use_chrome = kwargs.get("use_chrome", False)

        # proxies
        self.proxy_ip = kwargs.get("proxy_ip")
        self.proxy_port = kwargs.get("proxy_port")
        self.use_luminati = kwargs.get("use_luminati", False)
        self.use_proxy = kwargs.get("use_proxy", True)

        # dsh extension
        self._port_range = [24000, 24100]

        # execute parameters
        self.active = int(kwargs.get("active", 1))
        self.offset = int(kwargs.get("offset", 0))
        self.limit = int(kwargs.get("limit", 25))

    def start_playwright(self):
        playwright = sync_playwright().start()
        self.playwright = playwright

    def stop_playwright(self):
        if self.playwright:
            self.playwright.stop()

    @property
    def proxy_data(self):
        if self.use_luminati:
            proxy_data = {
                "server": settings.LUMINATI_DOMAIN,
                "username": settings.LUMINATI_USERNAME,
                "password": settings.LUMINATI_PASSWORD,
            }
        if self.use_proxy:
            proxy_data = {
                # "server": '{}:{}'.format(self.proxy_ip, self.proxy_port),
                # "username": settings.BUY_PROXIES_USERNAME,
                # "password": settings.BUY_PROXIES_PASSWORD
            }

        return proxy_data

    def create_browser(self):
        self.start_playwright()
        if self.use_chrome:
            browser = self.playwright.chromium.launch_persistent_context(
                headless=False,
                proxy=self.proxy_data,
                accept_downloads=True,
                user_data_dir=os.getcwd() + "/user_tmp",
                args=[
                    f"--disable-extensions-except=\
                        {os.getcwd()+'/extensions/dropship-helper'}",
                    f"--load-extension=\
                        {os.getcwd()+'/extensions/dropship-helper'}",
                ],
            )
        else:
            browser = self.playwright.firefox.launch(
                headless=False,
                # proxy=self.proxy_data,
                firefox_user_prefs={
                    "media.peerconnection.enabled": False,
                    "privacy.trackingprotection.enabled": True,
                    "privacy.trackingprotection.socialtracking.enabled": True,
                    "privacy.annotate_channels.strict_list.enabled": True,
                    "privacy.donottrackheader.enabled": True,
                    "privacy.sanitize.pending": [
                        {"id": "newtab-container", "itemsToClear": [], "options": {}}
                    ],
                    "devtools.toolbox.host": "bottom",
                },
            )
            context = browser.new_context(accept_downloads=True)
        self.browser = context

    def close_browser(self):
        if self.browser:
            self.browser.close()
        self.browser = None
        self.stop_playwright()

    def open_new_page(self):
        page = self.browser.new_page()
        page.set_default_navigation_timeout(60 * 1000)
        page.set_viewport_size(
            {
                "width": self._default_page_width + random.randint(0, 200),
                "height": self._default_page_height + random.randint(0, 200),
            }
        )
        self.page = page

    def go_to_link(self, link):
        try:
            self.page.goto(link)
        except Exception:
            self.page.reload()
            self.page.goto(link)
        self.page.wait_for_timeout(random.randint(1000, 5000))

    def insert_value(self, selector, value):
        self.page.type(selector, value, delay=random.randint(50, 100))
        self.page.wait_for_timeout(random.randint(1000, 5000))

    def wait_element_loading(self, selector, time=20000):
        self.page.wait_for_selector(selector, timeout=time)

    def reinsert_value(self, selector, value):
        self.page.focus(selector)
        self.page.dblclick(selector)
        self.page.press("Backspace")
        self.insert_value(selector, value)

    def hit_enter(self):
        self.page.keyboard.press("Enter")

    def check_element(self, selector):
        self.page.check(selector)

    def reload_page(self):
        self.page.reload(wait_until="load")

    def click_element(self, selector):
        self.page.click(selector, delay=random.randint(0, 10))
        self.page.wait_for_timeout(random.randint(1000, 3000))

    def select_option(self, selector, **kwargs):
        if kwargs.get("option_selector") == "label":
            self.page.select(selector, label=kwargs.get("option_value"))
        elif kwargs.get("option_selector") == "index":
            self.page.select(selector, index=kwargs.get("option_value"))
        elif kwargs.get("option_selector") == "value":
            self.page.select(selector, value=kwargs.get("option_value"))
        self.page.wait_for_timeout(random.randint(1000, 3000))

    def manage_proxy_by_dsh(self, flag, proxy_info=None):
        targets = self.browser.background_pages()
        dsh_extension = filter(self.get_dsh_extension, targets)
        ip = ""
        port = ""
        if proxy_info is None:
            ip = "127.0.0.1"
            port = str(random.choice(self._port_range))
        else:
            ip = proxy_info[0]
            port = proxy_info[1]

        if flag == "ON":
            content = "() => setProxyWebF({ip}, {port})".format(ip=ip, port=port)
            dsh_extension.evaluate(content)
        else:
            content = """() => { proxyOffWebF()}"""
            dsh_extension.evaluate(content)

    def sleep(self, seconds):
        time.sleep(seconds)

    @staticmethod
    def get_dsh_extension(target):
        if (
            target.get("title") == "STL Pro Dropship Helper"
            and target.get("type") == "background_page"
        ):
            return True
        return False
