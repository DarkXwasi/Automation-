import requests

class FacebookClient:
    def __init__(self, cookie, user_agent):
        self.session = requests.Session()
        self.base_url = "https://mbasic.facebook.com"
        self.cookie = cookie
        self.user_agent = user_agent
        self.session.headers.update({
            "User-Agent": self.user_agent,
            "Cookie": self.cookie,
        })

    def get(self, url, **kwargs):
        if not url.startswith("http"):
            url = self.base_url + url
        return self.session.get(url, **kwargs)

    def post(self, url, data=None, **kwargs):
        if not url.startswith("http"):
            url = self.base_url + url
        return self.session.post(url, data=data, **kwargs)

    def is_logged_in(self):
        """Check if login is valid by fetching the home page"""
        try:
            r = self.get("/")
            if "mbasic_logout_button" in r.text or "logout" in r.text.lower():
                return True
        except:
            return False
        return False

    def is_logged_in_response(self, response):
        """Check in response if session is still valid"""
        if response is None:
            return False
        if "login" in response.url or "password" in response.text.lower():
            return False
        return True