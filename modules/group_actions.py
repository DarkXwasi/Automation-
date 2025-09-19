import time
import random
import os
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, urljoin

BASE_URL = "https://mbasic.facebook.com"

def _is_post_link(href: str) -> bool:
    """Check if href looks like a post link"""
    if not href:
        return False
    return (
        "/story.php" in href and "story_fbid" in href
    ) or "/permalink/" in href or "/posts/" in href

def parse_posts_from_html(html: str):
    """Extract posts from group page HTML"""
    soup = BeautifulSoup(html, "html.parser")
    posts = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if not _is_post_link(href):
            continue

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

        full_url = href if href.startswith("http") else urljoin(BASE_URL, href)
        if postid:
            posts.append({"post_id": postid, "post_url": full_url})

    return posts

def find_next_page_link(html: str):
    """Find pagination link for next page"""
    soup = BeautifulSoup(html, "html.parser")

    # Priority: text-based pagination
    for a in soup.find_all("a", href=True):
        txt = (a.get_text() or "").strip().lower()
        if "see more posts" in txt or "older posts" in txt or "more posts" in txt or "see more" in txt:
            href = a["href"]
            return href if href.startswith("http") else urljoin(BASE_URL, href)

    # Backup: URL patterns like after= / m_s=
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if any(x in href for x in ["after=", "m_s", "page="]):
            return href if href.startswith("http") else urljoin(BASE_URL, href)

    return None

def fetch_all_posts(client, group_id, max_pages=10, logger=print, debug=True):
    """Fetch all posts from a group with pagination"""
    seen = set()
    posts = []
    page_url = f"/groups/{group_id}"
    pages = 0

    if debug and not os.path.exists("debug"):
        os.makedirs("debug")

    while page_url and pages < max_pages:
        pages += 1
        logger(f"[Pagination] Fetching page {pages}: {page_url}")
        try:
            r = client.get(page_url)
        except Exception as e:
            logger(f"[Pagination] Request failed: {e}")
            break

        if debug:
            filename = f"debug/debug_page_{pages}.html"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(r.text)
            logger(f"[Debug] Saved raw HTML -> {filename}")

        if not client.is_logged_in_response(r):
            logger(f"[Pagination] Not logged in or bad status: {getattr(r, 'status_code', None)}")
            break

        new_posts = parse_posts_from_html(r.text)
        added = 0
        for p in new_posts:
            pid = p.get("post_id")
            if pid and pid not in seen:
                seen.add(pid)
                posts.append(p)
                added += 1

        logger(f"[Pagination] Page {pages} -> found {len(new_posts)} posts, added {added}")

        next_link = find_next_page_link(r.text)
        if not next_link:
            logger("[Pagination] No next page link found, stopping.")
            break

        page_url = next_link.replace(BASE_URL, "")
        time.sleep(random.uniform(1.0, 2.0))

    logger(f"[Pagination] Completed. Total unique posts: {len(posts)} (pages fetched: {pages})")
    return posts

def auto_join_group(client, group_id, logger=print):
    """Try to join a group automatically"""
    url = f"{BASE_URL}/groups/{group_id}"
    try:
        r = client.get(url)
    except Exception as e:
        logger(f"[Join] Failed to open group page: {e}")
        return False

    soup = BeautifulSoup(r.text, "html.parser")
    join_link = None
    for a in soup.find_all("a", href=True):
        if "join" in (a.get_text() or "").lower():
            join_link = a["href"]
            break

    if not join_link:
        logger("[Join] Join button not found (maybe already joined?)")
        return False

    target = join_link if join_link.startswith("http") else urljoin(BASE_URL, join_link)
    r2 = client.get(target)
    if r2.status_code == 200:
        logger("[Join] Group join request sent ✅")
        return True
    else:
        logger(f"[Join] Failed with status {r2.status_code}")
        return False