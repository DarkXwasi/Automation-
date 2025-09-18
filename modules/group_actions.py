import time
import random
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, urljoin

def _is_post_link(href):
    if not href:
        return False
    return ("/story.php" in href and "story_fbid" in href) or "/permalink/" in href or "/posts/" in href

def parse_posts_from_html(html):
    soup = BeautifulSoup(html, "html.parser")  # ✅ changed from lxml
    posts = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if _is_post_link(href):
            postid = None
            if "story.php" in href and "story_fbid" in href:
                try:
                    q = parse_qs(urlparse(href).query)
                    postid = q.get("story_fbid", [None])[0]
                except:
                    postid = None
            else:
                parts = href.rstrip("/").split("/")
                for p in reversed(parts):
                    if p.isdigit():
                        postid = p
                        break
            full = href if href.startswith("http") else urljoin("https://mbasic.facebook.com", href)
            if postid:
                posts.append({"post_id": postid, "post_url": full})
    return posts

def find_next_page_link(html):
    soup = BeautifulSoup(html, "html.parser")  # ✅ changed
    candidates = []
    for a in soup.find_all("a", href=True):
        txt = (a.get_text() or "").strip().lower()
        href = a["href"]
        if any(k in txt for k in ("see more", "more posts", "older posts", "view more", "more")):
            candidates.append(href)
        if "after=" in href or "m_s" in href or "page="