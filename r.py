import os
import requests
import base64
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

TELEGRAM_BOT_TOKEN = "8419025231:AAFdAVLJaBUEo1Js5qoPLE8rOvuSB6EUJlw"


# ---------------- START ------------------

def start(update, context):
    update.message.reply_text(
        "Welcome!\n\n"
        "1️⃣ Send GitHub token:\n/token YOUR_TOKEN\n\n"
        "2️⃣ Send repo:\n/repo username/repo\n\n"
        "3️⃣ Upload your .py file directly.\n\n"
        "Bot will automatically:\n"
        "✔ Upload your py file to GitHub\n"
        "✔ Create workflow YAML\n"
        "✔ Enable auto-run"
    )


# ---------------- SAVE TOKEN ------------------

def save_token(update, context):
    if not context.args:
        update.message.reply_text("Use: /token GITHUB_TOKEN")
        return
    context.user_data["token"] = context.args[0]
    update.message.reply_text("GitHub token saved!")


# ---------------- SAVE REPO ------------------

def save_repo(update, context):
    if not context.args:
        update.message.reply_text("Use: /repo username/repo")
        return
    context.user_data["repo"] = context.args[0]
    update.message.reply_text("Repo saved! Now upload your .py file.")


# ---------------- HANDLE PY FILE UPLOAD ------------------

def handle_file(update, context):
    if "token" not in context.user_data:
        update.message.reply_text("First set token using /token")
        return

    if "repo" not in context.user_data:
        update.message.reply_text("Set repo using /repo username/repo")
        return

    file = update.message.document

    if not file.file_name.endswith(".py"):
        update.message.reply_text("Please upload a .py file only.")
        return

    py_name = file.file_name
    token = context.user_data["token"]
    repo = context.user_data["repo"]

    # Download file
    file_path = f"/tmp/{py_name}"
    file.get_file().download(custom_path=file_path)

    with open(file_path, "rb") as f:
        content = f.read()

    encoded = base64.b64encode(content).decode()

    # Upload PY file to GitHub
    url = f"https://api.github.com/repos/{repo}/contents/{py_name}"

    data = {
        "message": f"Upload {py_name}",
        "content": encoded
    }

    headers = {"Authorization": f"token {token}"}

    r = requests.put(url, json=data, headers=headers)

    if r.status_code not in (200, 201):
        update.message.reply_text(f"PY upload failed:\n{r.text}")
        return

    # Create YAML workflow
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

    encoded_yaml = base64.b64encode(yaml_content.encode()).decode()

    yaml_url = f"https://api.github.com/repos/{repo}/contents/.github/workflows/{yaml_name}"

    data_yaml = {
        "message": "Create workflow",
        "content": encoded_yaml
    }

    r2 = requests.put(yaml_url, json=data_yaml, headers=headers)

    if r2.status_code in (200, 201):
        update.message.reply_text(
            f"Done!\n\n✔ PY uploaded\n✔ Workflow created\n\n"
            f"File: {py_name}\nWorkflow: {yaml_name}"
        )
    else:
        update.message.reply_text(f"Workflow error:\n{r2.text}")


# ---------------- MAIN ------------------

def main():
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("token", save_token))
    dp.add_handler(CommandHandler("repo", save_repo))
    dp.add_handler(MessageHandler(Filters.document, handle_file))

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
