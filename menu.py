#!/usr/bin/env python3
import os
import sys
import json
from pyfiglet import Figlet

CONFIG_FILE = "config.json"

def show_banner():
    os.system("clear")
    f = Figlet(font="doom")
    print(f.renderText("WASI"))
    print("=" * 50)
    print("   Facebook Group Automation Tool")
    print("=" * 50)

def load_config():
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def save_config(cfg):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)

def add_account():
    cfg = load_config()
    uid = input("Enter Account UID: ").strip()
    cookie = input("Enter Account Cookie: ").strip()
    new_acc = {"uid": uid, "cookie": cookie, "active": True}
    cfg["accounts"].append(new_acc)
    save_config(cfg)
    print(f"✅ Account {uid} added successfully!")
    input("\n[Press Enter to return to menu]")

def change_group():
    cfg = load_config()
    new_gid = input("Enter New Group UID: ").strip()
    cfg["group"]["id"] = new_gid
    save_config(cfg)
    print(f"✅ Group UID updated to {new_gid}")
    input("\n[Press Enter to return to menu]")

def main_menu():
    while True:
        show_banner()
        print("1) Start Bot")
        print("2) Stop Bot")
        print("3) Edit Config")
        print("4) Add Account")
        print("5) Change Group UID")
        print("6) Exit")
        print("=" * 50)

        choice = input("Select option: ")

        if choice == "1":
            os.system("python3 main.py")
            input("\n[Press Enter to return to menu]")
        elif choice == "2":
            os.system("pkill -f main.py")
            print("🛑 Bot stopped!")
            input("\n[Press Enter to return to menu]")
        elif choice == "3":
            os.system("nano config.json")
        elif choice == "4":
            add_account()
        elif choice == "5":
            change_group()
        elif choice == "6":
            print("👋 Exiting...")
            sys.exit(0)
        else:
            print("⚠️ Invalid option, try again!")
            input("\n[Press Enter to return to menu]")

if __name__ == "__main__":
    main_menu()