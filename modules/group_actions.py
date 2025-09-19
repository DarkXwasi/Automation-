# modules/group_actions.py
import time
import random
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, urljoin

BASE = "https://mbasic.facebook.com"

# ---------- Helpers ----------
def _is_post_link(href):
    if not href:
        return False
    return ("/story.php" in href and "story_fbid" in href) or "/permalink/" in href or "/posts/" in href

def parse_posts_from_html(html):
    soup = BeautifulSoup(html, "html.parser")
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
            full = href if href.startswith("http") else urljoin(BASE, href)
            if postid:
                posts.append({"post_id": postid, "post_url": full})
    return posts

def find_next_page_link(html):
    soup = BeautifulSoup(html, "html.parser")
    for a in soup.find_all("a", href=True):
        txt = (a.get_text() or "").strip().lower()
        if "see more posts" in txt or "older posts" in txt or "more posts" in txt:
            href = a["href"]
            return href if href.startswith("http") else urljoin(BASE, href)
    return None

# ---------- Fetch Posts ----------
def fetch_all_posts(client, group_id, max_pages=5, logger=None, debug=False):
    seen = set()
    posts = []
    page_url = f"/groups/{group_id}"
    pages = 0

    while page_url and pages < max_pages:
        pages += 1
        if debug: print(f"[DEBUG] Fetching page {pages}: {page_url}")
        if logger: logger(f"[Pagination] Fetching page {pages}: {page_url}")

        try:
            r = client.get(page_url)
        except Exception as e:
            if debug: print(f"[DEBUG] Request failed: {e}")
            if logger: logger(f"[Pagination] Request failed: {e}")
            break

        if not getattr(client, "is_logged_in_response", lambda x: True)(r):
            if debug: print(f"[DEBUG] Not logged in or bad status: {getattr(r,'status_code',None)}")
            if logger: logger(f"[Pagination] Not logged in or bad status: {getattr(r,'status_code',None)}")
            break

        new_posts = parse_posts_from_html(r.text)
        for p in new_posts:
            pid = p.get("post_id")
            if pid and pid not in seen:
                seen.add(pid)
                posts.append(p)

        if debug: print(f"[DEBUG] Page {pages} -> total posts {len(posts)}")
        if logger: logger(f"[Pagination] Page {pages} -> total posts {len(posts)}")

        next_link = find_next_page_link(r.text)
        if not next_link:
            break
        if next_link.startswith(BASE):
            page_url = next_link.replace(BASE, "")
        else:
            page_url = next_link
        time.sleep(random.uniform(1.0, 2.0))

    if debug: print(f"[DEBUG] Completed. Total posts: {len(posts)}")
    if logger: logger(f"[Pagination] Completed. Total posts: {len(posts)}")
    return posts

# ---------- React ----------
def react_post_simple(client, post_id, reaction="like", logger=None, dry_run=True):
    if dry_run:
        if logger: logger(f"[DRY RUN] Would react {reaction} on {post_id}")
        return True, "dry_run"

    post_url = f"{BASE}/story.php?story_fbid={post_id}"
    try:
        r = client.get(post_url)
        if r.status_code != 200:
            return False, f"status_{r.status_code}"
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.find_all("a", href=True):
            if a.get_text().strip().lower() == reaction.lower():
                link = a["href"]
                target = link if link.startswith("http") else BASE + link
                r2 = client.get(target)
                return r2.status_code == 200, f"status_{r2.status_code}"
        return False, "reaction_not_found"
    except Exception as e:
        if logger: logger(f"[React] Error: {e}")
        return False, str(e)

# ---------- Comment ----------
def comment_on_post(client, post_id, text, logger=None, dry_run=True):
    if dry_run:
        if logger: logger(f"[DRY RUN] Would comment '{text}' on {post_id}")
        return True, "dry_run"

    post_url = f"{BASE}/story.php?story_fbid={post_id}"
    try:
        r = client.get(post_url)
        if r.status_code != 200:
            return False, f"status_{r.status_code}"

        soup = BeautifulSoup(r.text, "html.parser")
        form = None
        for f in soup.find_all("form", action=True):
            if f.find("input", {"name": "comment_text"}):
                form = f
                break

        if not form:
            return False, "comment_form_not_found"

        action = form.get("action")
        if not action.startswith("http"):
            action = urljoin(BASE, action)

        data = {}
        for inp in soup.find_all("input"):
            name = inp.get("name")
            value = inp.get("value", "")
            if name == "comment_text":
                value = text
            if name:
                data[name] = value

        r2 = client.post(action, data=data)
        return (r2.status_code == 200), f"commented:{r2.status_code}"
    except Exception as e:
        if logger: logger(f"[Comment] Error: {e}")
        return False, str(e)