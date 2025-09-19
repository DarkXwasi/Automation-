import time
import random
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, urljoin

# ✅ Check if href looks like a post
def _is_post_link(href):
    if not href:
        return False
    return (
        "story_fbid=" in href
        or "/posts/" in href
        or "/permalink/" in href
        or "mbasic.facebook.com/story.php" in href
    )

# ✅ Parse posts
def parse_posts_from_html(html):
    soup = BeautifulSoup(html, "html.parser")
    posts = []

    for a in soup.find_all("a", href=True):
        href = a["href"]
        if _is_post_link(href):
            postid = None

            if "story_fbid=" in href:
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

    # ✅ Debugging
    if not posts:
        print("[DEBUG] No posts found — saving HTML to debug_page.html")
        with open("debug_page.html", "w", encoding="utf-8") as f:
            f.write(html[:5000])  # save first 5k chars to check

    return posts

# ✅ Next page finder
def find_next_page_link(html):
    soup = BeautifulSoup(html, "html.parser")
    for a in soup.find_all("a", href=True):
        txt = (a.get_text() or "").strip().lower()
        if "see more posts" in txt or "older posts" in txt or "more posts" in txt:
            href = a["href"]
            return href if href.startswith("http") else urljoin("https://mbasic.facebook.com", href)
    return None

# ✅ Fetch all posts with pagination
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

# ✅ Auto join group
def auto_join_group(client, group_id, logger=None):
    join_url = f"https://mbasic.facebook.com/groups/{group_id}"
    try:
        r = client.get(join_url)
        if r.status_code != 200:
            return False, f"status_{r.status_code}"

        soup = BeautifulSoup(r.text, "html.parser")
        join_link = None
        for a in soup.find_all("a", href=True):
            txt = (a.get_text() or "").strip().lower()
            if "join group" in txt:
                join_link = a["href"]
                break

        if not join_link:
            return False, "no_join_button"

        target = join_link if join_link.startswith("http") else "https://mbasic.facebook.com" + join_link
        r2 = client.get(target)
        return (r2.status_code == 200), f"join_status_{r2.status_code}"
    except Exception as e:
        if logger: logger(f"[JoinGroup] error: {e}")
        return False, str(e)