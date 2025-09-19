import time
import random
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, urljoin

# -----------------------------
# ✅ Post Link Detector
# -----------------------------
def _is_post_link(href):
    if not href:
        return False
    return ("/story.php" in href and "story_fbid" in href) or "/permalink/" in href or "/posts/" in href


# -----------------------------
# ✅ Parse Posts
# -----------------------------
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
            full = href if href.startswith("http") else urljoin("https://mbasic.facebook.com", href)
            if postid:
                posts.append({"post_id": postid, "post_url": full})
    return posts


# -----------------------------
# ✅ Find Next Page
# -----------------------------
def find_next_page_link(html):
    soup = BeautifulSoup(html, "html.parser")
    for a in soup.find_all("a", href=True):
        txt = (a.get_text() or "").strip().lower()
        if "see more posts" in txt or "older posts" in txt or "more posts" in txt:
            href = a["href"]
            return href if href.startswith("http") else urljoin("https://mbasic.facebook.com", href)
    return None


# -----------------------------
# ✅ Fetch All Posts
# -----------------------------
def fetch_all_posts(client, group_id, max_pages=20, logger=None):
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


# -----------------------------
# ✅ Comment on Post
# -----------------------------
def comment_on_post(client, post_id, text, logger=None, retries=3):
    post_url = f"https://mbasic.facebook.com/story.php?story_fbid={post_id}"
    attempt = 0
    while attempt < retries:
        attempt += 1
        try:
            r = client.get(post_url)
        except Exception as e:
            if logger: logger(f"[Comment] Request error on post {post_id}: {e}")
            time.sleep(1 + attempt)
            continue
        if r.status_code != 200:
            return False, f"status_{r.status_code}"

        soup = BeautifulSoup(r.text, "html.parser")
        form = None
        for f in soup.find_all("form", action=True):
            if f.find("input", {"name": "comment_text"}) or "comment" in (f.get("action") or ""):
                form = f
                break
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
                return True, "posted"
        except Exception as e:
            if logger: logger(f"[Comment] post error on {post_id}: {e}")
            time.sleep(1 + attempt)
    return False, "failed_after_retries"


# -----------------------------
# ✅ React on Post (All Reactions)
# -----------------------------
def react_post_simple(client, post_id, reaction="like", logger=None, retries=3):
    """
    React on a post with a given reaction.
    Supported: like, love, care, haha, wow, sad, angry
    """
    post_url = f"https://mbasic.facebook.com/story.php?story_fbid={post_id}"
    attempt = 0
    while attempt < retries:
        attempt += 1
        try:
            r = client.get(post_url)
        except Exception as e:
            if logger: logger(f"[React] Request error on {post_id}: {e}")
            continue

        if r.status_code != 200:
            if logger: logger(f"[React] Failed to open post {post_id}, status {r.status_code}")
            continue

        soup = BeautifulSoup(r.text, "html.parser")

        react_link = None
        for a in soup.find_all("a", href=True):
            href = a["href"].lower()
            txt = (a.get_text() or "").lower()

            if reaction == "like" and ("like this" in txt or txt == "like"):
                react_link = a["href"]
                break

            if "reaction_type=" in href and reaction in href:
                react_link = a["href"]
                break

        if not react_link:
            if logger: logger(f"[React] No {reaction} link found")
            return False

        target = react_link if react_link.startswith("http") else "https://mbasic.facebook.com" + react_link
        try:
            r2 = client.get(target)
            if r2.status_code == 200:
                if logger: logger(f"[React] Reacted with {reaction} on {post_id}")
                return True
        except Exception as e:
            if logger: logger(f"[React] Follow error: {e}")

    return False


# -----------------------------
# ✅ Auto Join Group
# -----------------------------
def join_group(client, group_id, logger=None):
    group_url = f"https://mbasic.facebook.com/groups/{group_id}"
    try:
        r = client.get(group_url)
        soup = BeautifulSoup(r.text, "html.parser")
        join_link = None
        for a in soup.find_all("a", href=True):
            if "join" in (a.get_text() or "").lower():
                join_link = a["href"]
                break
        if not join_link:
            if logger: logger(f"[Join] No join button found for group {group_id}")
            return False
        target = join_link if join_link.startswith("http") else "https://mbasic.facebook.com" + join_link
        r2 = client.get(target)
        if r2.status_code == 200:
            if logger: logger(f"[Join] Successfully sent join request for group {group_id}")
            return True
    except Exception as e:
        if logger: logger(f"[Join] Error joining group {group_id}: {e}")
    return False