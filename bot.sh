#!/bin/bash

case "$1" in
  start)
    echo "🚀 Starting Facebook Automation Bot..."
    python main.py > output.log 2>&1 &
    echo $! > bot.pid
    echo "✅ Bot started (PID=$(cat bot.pid)). Logs -> output.log"
    ;;
  stop)
    if [ -f bot.pid ]; then
      kill $(cat bot.pid)
      rm bot.pid
      echo "🛑 Bot stopped."
    else
      echo "⚠️ No bot running."
    fi
    ;;
  status)
    if [ -f bot.pid ]; then
      echo "📌 Bot running with PID=$(cat bot.pid)"
    else
      echo "❌ Bot not running."
    fi
    ;;
  logs)
    tail -f output.log
    ;;
  *)
    echo "Usage: ./bot.sh {start|stop|status|logs}"
    ;;
esac