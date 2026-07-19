import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, StaleElementReferenceException,
    NoAlertPresentException, WebDriverException
)
import utils


class StopRequested(Exception):
    pass


class EverytimeCleaner:
    def __init__(self, config, logger=None, stop_flag=None):
        self.config = config
        self.log = logger or (lambda m, lv="info": print(m))
        self.stop_flag = stop_flag

        self.deleted_count = 0
        self.failed_count = 0
        self.processed = 0
        self.total_targets = 0

        self.driver = self._init_driver()
        self.wait = WebDriverWait(self.driver, 10)

    def _check_stop(self):
        if self.stop_flag and self.stop_flag.is_set():
            raise StopRequested()

    def _sleep(self, lo, hi):
        """중지 요청에 빠르게 반응하는 분할 대기"""
        end = time.time() + utils.rand_delay(lo, hi)
        while time.time() < end:
            self._check_stop()
            time.sleep(0.1)

    # ── 드라이버 ─────────────────────────
    def _build_options(self):
        o = Options()
        o.add_argument('--no-sandbox')
        o.add_argument('--disable-dev-shm-usage')
        o.add_argument('--disable-gpu')
        o.add_argument('--disable-blink-features=AutomationControlled')
        o.add_experimental_option("excludeSwitches", ["enable-automation"])
        o.add_experimental_option('useAutomationExtension', False)
        if self.config.get("HEADLESS", False):
            o.add_argument('--headless=new')
        return o

    def _init_driver(self):
        try:
            return webdriver.Chrome(options=self._build_options())
        except WebDriverException as e:
            self.log(f"Selenium Manager 실패: {e}", "warn")

        try:
            from webdriver_manager.chrome import ChromeDriverManager
            svc = Service(ChromeDriverManager().install())
            return webdriver.Chrome(service=svc, options=self._build_options())
        except Exception as e:
            self.log(f"webdriver_manager 실패: {e}", "warn")

        for name in ("chromedriver.exe", "chromedriver"):
            p = utils.get_resource_path(name)
            if os.path.exists(p):
                return webdriver.Chrome(service=Service(p),
                                        options=self._build_options())

        raise RuntimeError(
            "ChromeDriver 초기화 실패.\n"
            "Chrome 설치 여부와 인터넷 연결을 확인하거나,\n"
            "chromedriver.exe를 실행 파일과 같은 폴더에 두세요.")

    # ── 로그인 ───────────────────────────
    def login(self, timeout=300):
        self.driver.get("https://everytime.kr/login")
        time.sleep(2.0)

        start = time.time()
        notified = False
        while "login" in self.driver.current_url or "2fa" in self.driver.current_url:
            self._check_stop()
            if time.time() - start > timeout:
                raise TimeoutError("로그인 대기 시간을 초과했습니다 (5분).")
            if not notified:
                self.log("브라우저 창에서 로그인·인증을 완료해 주세요.", "warn")
                notified = True
            time.sleep(1.0)
        self.log("인증 완료.", "ok")

    # ── 삭제 ─────────────────────────────
    def _accept_alert(self, timeout=5):
        try:
            WebDriverWait(self.driver, timeout).until(EC.alert_is_present())
            self.driver.switch_to.alert.accept()
            return True
        except (TimeoutException, NoAlertPresentException):
            return False

    def delete_logic(self, url, max_rounds=30):
        self.driver.get(url)
        self._sleep(2.0, 3.0)

        deleted_any = False
        for _ in range(max_rounds):
            self._check_stop()
            try:
                btns = self.driver.find_elements(
                    By.CSS_SELECTOR, ".comments .del, article.my .del")
                visible = [b for b in btns if b.is_displayed()]
            except StaleElementReferenceException:
                self._sleep(0.5, 1.0)
                continue

            if not visible:
                break

            btn = visible[0]
            try:
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});", btn)
                self._sleep(0.4, 0.8)
                self.driver.execute_script("arguments[0].click();", btn)

                if not self._accept_alert():
                    self.log("확인창이 나타나지 않아 건너뜁니다.", "warn")
                    break

                deleted_any = True
                self._sleep(0.8, 1.4)
            except StopRequested:
                raise
            except StaleElementReferenceException:
                self._sleep(0.4, 0.8)
                continue
            except Exception as e:
                self.log(f"삭제 중 오류: {e}", "warn")
                break

        return deleted_any

    def clean_all(self):
        pages = [("내가 쓴 글", "https://everytime.kr/myarticle"),
                 ("내가 쓴 댓글", "https://everytime.kr/mycommentarticle")]
        failed = set()

        try:
            for title, page_url in pages:
                self.log(f"── {title} 탐색", "step")
                retry = 0

                while True:
                    self._check_stop()
                    self.driver.get(page_url)
                    self._sleep(2.5, 3.5)

                    els = self.driver.find_elements(By.CSS_SELECTOR, "a.article")

                    if not els:
                        if retry < 2:
                            retry += 1
                            self.log(f"목록을 찾지 못했습니다. 재시도 {retry}/2", "warn")
                            self._sleep(2.0, 3.0)
                            continue
                        self.log(f"{title}: 삭제할 항목이 없습니다.", "ok")
                        break
                    retry = 0

                    links = []
                    for el in els:
                        try:
                            href = el.get_attribute("href")
                        except StaleElementReferenceException:
                            continue
                        if not href or "/lecture/" in href or href in failed:
                            continue
                        links.append(href)
                    links = list(dict.fromkeys(links))

                    if not links:
                        self.log(f"{title}: 남은 항목이 없습니다.", "ok")
                        break

                    self.total_targets = self.processed + len(links)

                    for link in links:
                        self._check_stop()
                        if self.delete_logic(link):
                            self.deleted_count += 1
                            self.log(f"삭제 완료  {link}", "ok")
                        else:
                            self.failed_count += 1
                            failed.add(link)
                            self.log(f"삭제 실패  {link}", "warn")
                        self.processed += 1
                        self._sleep(self.config.get("MIN_DELAY", 1.5),
                                    self.config.get("MAX_DELAY", 3.0))
        except StopRequested:
            self.log("중지되었습니다.", "warn")

    def close(self):
        d = getattr(self, "driver", None)
        if d:
            try:
                d.quit()
            except Exception:
                pass
            self.driver = None
