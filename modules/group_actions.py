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
        if "after=" in href or "m_s" in href or "page=" in href:
            candidates.append(href)
    for h in candidates:
        if h:
            return h if h.startswith("http") else urljoin("https://mbasic.facebook.com", h)
    return None

def fetch_all_posts(client, group_id, max_pages=50, logger=None):
    seen = set()
    posts = []
    page_url = f"/groups/{group_id}"
    pages = 0

    while page_url and pages < max_pages:
        pages += 1
        if logger: logger(f"[Pagination] Fetching page {pages}: {page_url}")
        try:
            r = client.get(page_url)
        except Exception as e:
            if logger: logger(f"[Pagination] Request failed: {e}")
            break
        if not client.is_logged_in_response(r):
            if logger: logger(f"[Pagination] Not logged in or bad status: {getattr(r,'status_code',None)}")
            break

        new_posts = parse_posts_from_html(r.text)
        added = 0
        for p in new_posts:
            pid = p.get("post_id")
            if pid and pid not in seen:
                seen.add(pid)
                posts.append(p)
                added += 1