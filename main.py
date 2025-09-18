#!/usr/bin/env python3
import random
import time
from modules.loader import load_config, load_processed, save_processed
from modules.fb_client import FBClient
from modules.group_actions import fetch_all_posts, react_post_simple, comment_on_post
from modules.logger import setup, info, warn, error, exception

def main():
    cfg = load_config()
    settings = cfg.get("settings", {})
    setup(settings.get("log_file", "logs/fb-bot.log"))

    dry_run = cfg.get("dry_run", True)
    group_cfg = cfg.get("group", {})
    group_id = group_cfg.get("id")
    max_pages = group_cfg.get("max_pages", 50)

    if not group_id:
        error("No group id in config.json")
        return

    # load processed state
    processed = load_processed()

    # choose an account to fetch posts
    fetch_client = None
    fetch_account_uid = None
    for a in cfg.get("accounts", []):
        if a.get("active") and a.get("cookie"):
            fetch_client = FBClient(a["cookie"], user_agent=settings.get("user_agent"))
            fetch_account_uid = a.get("uid")
            info(f"Using account {fetch_account_uid} to fetch posts")
            break
    if not fetch_client:
        error("No active account with cookie found to fetch posts")
        return

    posts = fetch_all_posts(fetch_client, group_id, max_pages=max_pages, logger=info)
    if not posts:
        error("No posts found or fetch failed")
        return

    info(f"[Group {group_id}] Total posts to process: {len(posts)}")

    # ensure processed structure keys exist
    for a in cfg.get("accounts", []):
        uid = a.get("uid")
        if uid not in processed:
            processed[uid] = []

    # Iterate over accounts; each account will act on ALL fetched posts
    for acc in cfg.get("accounts", []):
        uid = acc.get("uid")
        if not acc.get("active"):
            info(f"Skipping inactive account {uid}")
            continue
        cookie = acc.get("cookie")
        if not cookie:
            warn(f"No cookie for account {uid}, skipping")
            continue

        client = FBClient(cookie, user_agent=settings.get("user_agent"))
        info(f"\n=== Using account {uid} ===")

        max_actions = settings.get("max_actions_per_account", 0)
        action_count = 0

        for idx, p in enumerate(posts, start=1):
            post_id = p.get("post_id")

            # skip if this account already processed this post
            if post_id in processed.get(uid, []):
                info(f"[{idx}/{len(posts)}] Account {uid} -> Already processed post {post_id}, skipping")
                continue

            info(f"[{idx}/{len(posts)}] Account {uid} -> Reacting on post {post_id}")

            chosen_react = random.choice(group_cfg.get("reactions", [])) if group_cfg.get("reactions") else None
            if chosen_react:
                if dry_run:
                    info(f"[DRY RUN] Would react ({chosen_react}) on {post_id}")
                    react_ok, react_info = True, "dry_run"
                else:
                    try:
                        react_ok, react_info = react_post_simple(client, post_id, logger=info)
                    except Exception as e:
                        exception(f"Exception reacting on {post_id}: {e}")
                        react_ok, react_info = False, str(e)

                if react_ok:
                    info(f"Reacted ({chosen_react}) on {post_id} -> {react_info}")
                else:
                    warn(f"React failed on {post_id} -> {react_info}")

            rmin = settings.get("reaction_delay_min", 4)
            rmax = settings.get("reaction_delay_max", 8)
            time.sleep(random.uniform(rmin, rmax))

            chosen_comment = random.choice(group_cfg.get("comment_texts", [])) if group_cfg.get("comment_texts") else ""
            if chosen_comment:
                if dry_run:
                    info(f"[DRY RUN] Would comment on {post_id}: {chosen_comment}")
                    c_ok, c_info = True, "dry_run"
                else:
                    try:
                        c_ok, c_info = comment_on_post(client, post_id, chosen_comment, logger=info)
                    except Exception as e:
                        exception(f"Exception commenting on {post_id}: {e}")
                        c_ok, c_info = False, str(e)

                if c_ok:
                    info(f"Commented on {post_id}: {chosen_comment} -> {c_info}")
                else:
                    warn(f"Comment failed on {post_id} -> {c_info}")

            cmin = settings.get("comment_delay_min", 8)
            cmax = settings.get("comment_delay_max", 12)
            time.sleep(random.uniform(cmin, cmax))

            # record processed only if not dry_run and at least one of react/comment succeeded
            if not dry_run:
                # mark processed whether success or not? We'll mark only if comment succeeded or react succeeded
                # choose to mark if either action succeeded
                if ('react_ok' in locals() and react_ok) or ('c_ok' in locals() and c_ok):
                    processed.setdefault(uid, []).append(post_id)
                    save_processed(processed)
                    info(f"Saved progress: account {uid} -> {post_id}")

            action_count += 1
            if max_actions > 0 and action_count >= max_actions:
                info(f"Reached max_actions_per_account ({max_actions}) for {uid}, stopping for this account")
                break

        info(f"=== Done account {uid} ===")
        time.sleep(2)

    info("All accounts processed")

if __name__ == "__main__":
    main()