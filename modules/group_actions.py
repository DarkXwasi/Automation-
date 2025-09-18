# modules/group_actions.py
import time
import random
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, urljoin

def _is_post_link(href):
    if not href:
        return False
    return ("/story.php" in href and "story_fbid" in href) or "/permalink/" in href or "/posts/" in href

def parse_posts_from_html(html):
    soup = BeautifulSoup(html, "lxml")
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
    soup = BeautifulSoup(html, "lxml")
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
        if logger: logger(f"[Pagination] Page {pages} -> found {len(new_posts)} posts, added {added}")

        next_link = find_next_page_link(r.text)
        if not next_link:
            break
        if next_link.startswith("https://mbasic.facebook.com"):
            page_url = next_link.replace("https://mbasic.facebook.com", "")
        else:
            page_url = next_link
        time.sleep(random.uniform(1.0, 2.0))

    if logger: logger(f"[Pagination] Completed. Total unique posts: {len(posts)} (pages fetched: {pages})")
    return posts

def react_post_simple(client, post_id, logger=None, retries=3):
    post_url = f"https://mbasic.facebook.com/story.php?story_fbid={post_id}"
    attempt = 0
    while attempt < retries:
        attempt += 1
        try:
            r = client.get(post_url)
        except Exception as e:
            if logger: logger(f"[React] Request error on post {post_id}: {e} (attempt {attempt})")
            time.sleep(1 + attempt)
            continue
        if r.status_code != 200:
            return False, f"status_{r.status_code}"
        soup = BeautifulSoup(r.text, "lxml")
        like_link = None
        for a in soup.find_all("a", href=True):
            text = (a.get_text() or "").strip().lower()
            if text == "like" or "like this" in text or text.startswith("like"):
                like_link = a["href"]
                break
        if not like_link:
            for a in soup.find_all("a", href=True):
                if "reaction" in a["href"] or "ufi/reaction" in a["href"]:
                    like_link = a["href"]
                    break
        if not like_link:
            return False, "no_like_link"
        target = like_link if like_link.startswith("http") else ("https://mbasic.facebook.com" + like_link)
        try:
            r2 = client.get(target)
            return (r2.status_code == 200), f"followed:{r2.status_code}"
        except Exception as e:
            if logger: logger(f"[React] follow error on post {post_id}: {e} (attempt {attempt})")
            time.sleep(1 + attempt)
    return False, "failed_after_retries"

def comment_on_post(client, post_id, text, logger=None, retries=3):
    post_url = f"https://mbasic.facebook.com/story.php?story_fbid={post_id}"
    attempt = 0
    while attempt < retries:
        attempt += 1
        try:
            r = client.get(post_url)
        except Exception as e:
            if logger: logger(f"[Comment] Request error on post {post_id}: {e} (attempt {attempt})")
            time.sleep(1 + attempt)
            continue
        if r.status_code != 200:
            return False, f"status_{r.status_code}"
        soup = BeautifulSoup(r.text, "lxml")
        form = None
        for f in soup.find_all("form", action=True):
            if f.find("input", {"name": "comment_text"}) or "comment" in (f.get("action") or ""):
                form = f
                break
        if form is None:
            form = soup.find("form", action=True)
        if form is None:
            return False, "no_comment_form"
        action = form.get("action")
        if not action.startswith("http"):
            action = "https://mbasic.facebook.com" + action
        data = {}
        for inp in form.find_all("input"):
            name = inp.get("name")
            if not name:
                continue
            value = inp.get("value", "")
            data[name] = value
        data["comment_text"] = text
        try:
            r2 = client.post(action, data=data)
            if r2.status_code == 200:
                if text in r2.text:
                    return True, "posted"
                return True, "posted_but_not_verified"
            else:
                if logger: logger(f"[Comment] status {r2.status_code} on post {post_id} (attempt {attempt})")
                time.sleep(1 + attempt)
                continue
        except Exception as e:
            if logger: logger(f"[Comment] post error on post {post_id}: {e} (attempt {attempt})")
            time.sleep(1 + attempt)
    return False, "failed_after_retries"
