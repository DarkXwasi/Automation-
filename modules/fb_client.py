# modules/fb_client.py
import requests

class FBClient:
    def __init__(self, cookie: str, user_agent: str = None):
        self.session = requests.Session()
        headers = {
            "User-Agent": user_agent or "Mozilla/5.0",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Connection": "keep-alive"
        }
        self.session.headers.update(headers)
        # set cookie header
        self.session.headers.update({"Cookie": cookie})
        self.base = "https://mbasic.facebook.com"

    def get(self, path_or_url, **kwargs):
        url = path_or_url if path_or_url.startswith("http") else (self.base + path_or_url)
        return self.session.get(url, timeout=25, **kwargs)

    def post(self, path_or_url, data=None, **kwargs):
        url = path_or_url if path_or_url.startswith("http") else (self.base + path_or_url)
        return self.session.post(url, data=data or {}, timeout=25, **kwargs)

    def is_logged_in_response(self, resp):
        # simple check: if redirected to login page or url contains 'login'
        try:
            if resp is None:
                return False
            if "login" in resp.url.lower():
                return False
            if resp.status_code != 200:
                return False
            # if page contains "Log in" text strongly indicating login, conservative check
            text = resp.text.lower()[:1500]
            if "log in" in text and ("facebook" in text):
                return False
            return True
        except Exception:
            return False

