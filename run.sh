#!/bin/bash
clear
echo -e "\e[1;36m======================================\e[0m"
echo -e "\e[1;32m         🔥 WASI FB BOT 🔥          \e[0m"
echo -e "\e[1;36m======================================\e[0m"
echo
echo -e "\e[1;33m[+] Updating repository from GitHub...\e[0m"
git pull
echo
echo -e "\e[1;32m[+] Starting Bot...\e[0m"
python main.py