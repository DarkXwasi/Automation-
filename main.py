import json
import random
import time
from modules.group_actions import fetch_all_posts, react_post_simple, comment_on_post
from modules.client import FacebookClient  # ✅ assume tumhare paas client hai


# Logger function
def log(msg):
    print(msg)


def main():
    # Load config.json
    with open("config.json", "r") as f:
        config = json.load(f)

    accounts = [a for a in config["accounts"] if a.get("active")]
    group_id = config["group"]["id"]
    comments = config["group"]["comment_texts"]
    reactions = config["group"]["reactions"]
    max_pages = config["group"].get("max_pages", 50)

    log(f"[Config] Loaded {len(accounts)} active accounts.")
    log(f"[Config] Target Group: {group_id}")

    # Process each account
    for acc in accounts:
        uid = acc["uid"]
        cookie = acc["cookie"]
        log(f"\n[Account] Starting for UID {uid}...")

        # Login client
        client = FacebookClient(cookie, config["settings"]["user_agent"])
        if not client.is_logged_in():
            log(f"[Login] Failed for UID {uid}, skipping.")
            continue

        # Fetch posts
        posts = fetch_all_posts(client, group_id, max_pages=max_pages, logger=log)
        if not posts:
            log(f"[Posts] No posts found for group {group_id}.")
            continue

        log(f"[Posts] Found {len(posts)} posts in group {group_id}")

        # Loop through posts
        for idx, post in enumerate(posts, 1):
            pid = post["post_id"]
            purl = post["post_url"]
            log(f"\n[Post {idx}] {purl}")

            # React
            reaction = random.choice(reactions)
            ok, msg = react_post_simple(client, pid, logger=log)
            log(f"[React] Reaction={reaction}, Status={ok}, Msg={msg}")

            # Comment
            text = random.choice(comments)
            ok, msg = comment_on_post(client, pid, text, logger=log)
            log(f"[Comment] Text='{text}', Status={ok}, Msg={msg}")

            # Delay (anti-ban)
            rdelay = random.randint(
                config["settings"]["reaction_delay_min"],
                config["settings"]["reaction_delay_max"],
            )
            cdelay = random.randint(
                config["settings"]["comment_delay_min"],
                config["settings"]["comment_delay_max"],
            )
            total_sleep = rdelay + cdelay
            log(f"[Delay] Sleeping {total_sleep} seconds...")
            time.sleep(total_sleep)


if __name__ == "__main__":
    main()