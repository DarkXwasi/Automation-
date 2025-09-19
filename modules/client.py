import requests

class FBClient:
    def __init__(self, cookie, user_agent=None):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": user_agent or "Mozilla/5.0 (Linux; Android 10; Mobile) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Mobile Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        })
        self.session.headers.update({"Cookie": cookie})

    def get(self, url, **kwargs):
        if not url.startswith("http"):
            url = "https://mbasic.facebook.com" + url
        return self.session.get(url, **kwargs)

    def post(self, url, data=None, **kwargs):
        if not url.startswith("http"):
            url = "https://mbasic.facebook.com" + url
        return self.session.post(url, data=data, **kwargs)

    def is_logged_in_response(self, response):
        """Check if cookie is still valid"""
        if "mbasic_logout_button" in response.text or "home.php" in response.text:
            return True
        return response.status_code == 200