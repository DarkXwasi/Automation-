import os
import json
import time
import random
from modules.group_actions import fetch_all_posts, comment_on_post, react_post_simple, join_group
from modules.client import FBClient

CONFIG_FILE = "config.json"

def load_config():
    if not os.path.exists(CONFIG_FILE):
        print("❌ Config file not found!")
        return None
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

def clear_screen():
    os.system("clear" if os.name == "posix" else "cls")

def print_banner():
    print("══════════════════════════════════════════════")
    print("      ✨🔥 W A S I   A U T O M A T I O N 🔥✨   ")
    print("══════════════════════════════════════════════")

def menu():
    clear_screen()
    print_banner()
    print("\n[1] Fetch Posts")
    print("[2] React on Posts")
    print("[3] Comment on Posts")
    print("[4] Join Group")
    print("[5] Exit\n")
    choice = input("👉 Select option: ")
    return choice

def main():
    config = load_config()
    if not config:
        return

    accounts = config.get("accounts", [])
    group = config.get("group", {})
    settings = config.get("settings", {})

    if not accounts:
        print("❌ No accounts found in config.json")
        return

    account = accounts[0]
    client = FBClient(account["cookie"], settings.get("user_agent", None))

    while True:
        choice = menu()

        # ✅ Fetch Posts
        if choice == "1":
            posts = fetch_all_posts(client, group["id"], max_pages=group.get("max_pages", 5), logger=print)
            print(f"✅ Total {len(posts)} posts fetched")
            input("\nPress Enter to continue...")

        # ✅ React
        elif choice == "2":
            posts = fetch_all_posts(client, group["id"], max_pages=1, logger=print)
            for p in posts:
                reaction = random.choice(group.get("reactions", ["like"]))
                react_post_simple(client, p["post_id"], reaction, logger=print)
                time.sleep(random.uniform(settings["reaction_delay_min"], settings["reaction_delay_max"]))
            input("\n✅ Reactions done! Press Enter...")

        # ✅ Comment
        elif choice == "3":
            posts = fetch_all_posts(client, group["id"], max_pages=1, logger=print)
            for p in posts:
                text = random.choice(group.get("comment_texts", ["🔥🔥🔥"]))
                comment_on_post(client, p["post_id"], text, logger=print)
                time.sleep(random.uniform(settings["comment_delay_min"], settings["comment_delay_max"]))
            input("\n✅ Comments done! Press Enter...")

        # ✅ Join Group
        elif choice == "4":
            join_group(client, group["id"], logger=print)
            input("\n✅ Join request sent! Press Enter...")

        elif choice == "5":
            print("👋 Exiting... Bye Waseem 👑")
            break

        else:
            print("❌ Invalid choice!")
            time.sleep(1)

if __name__ == "__main__":
    main()