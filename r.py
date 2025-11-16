import os
import requests
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

TOKEN = "8419025231:AAFdAVLJaBUEo1Js5qoPLE8rOvuSB6EUJlw"

# Step 1: start command
def start(update, context):
    update.message.reply_text(
        "Send me your GitHub token in this format:\n\n"
        "/settoken YOUR_GITHUB_TOKEN"
    )

# Step 2: Save GitHub token
def settoken(update, context):
    if len(context.args) == 0:
        update.message.reply_text("Please send token like: /settoken TOKEN")
        return
    
    github_token = context.args[0]
    context.user_data["token"] = github_token

    update.message.reply_text(
        "Token saved!\n\nNow send your python filename like:\n"
        "/run mybot.py repo-name"
    )

# Step 3: Create YAML workflow automatically
def run(update, context):
    if "token" not in context.user_data:
        update.message.reply_text("First set your token using /settoken")
        return

    try:
        py_name = context.args[0]
        repo = context.args[1]
    except:
        update.message.reply_text("Use format:\n/run file.py repo-name")
        return

    token = context.user_data["token"]

    yaml_name = py_name.replace(".py", "") + ".yml"

    yaml_content = f"""
name: Auto Run {py_name}

on:
  workflow_dispatch:

jobs:
  run:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    - run: python {py_name}
"""

    url = f"https://api.github.com/repos/{repo}/contents/.github/workflows/{yaml_name}"

    # Encode content
    import base64
    data = {
        "message": "Auto-created workflow",
        "content": base64.b64encode(yaml_content.encode()).decode()
    }

    headers = {"Authorization": f"token {token}"}

    response = requests.put(url, json=data, headers=headers)

    if response.status_code in [200, 201]:
        update.message.reply_text(f"Workflow created!\nFile: {yaml_name}\nRepo: {repo}")
    else:
        update.message.reply_text(f"Error: {response.text}")

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("settoken", settoken))
    dp.add_handler(CommandHandler("run", run))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
