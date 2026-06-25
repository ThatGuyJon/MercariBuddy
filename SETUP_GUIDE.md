# MercariBuddy Setup Guide

This guide will walk you through the process of setting up, configuring, and running your MercariBuddy Discord Bot.

---

## 🛠️ Prerequisites

Before you start, make sure you have the following installed on your computer:
1. **Python 3.10 or higher** (Python 3.12 is fully supported). 
   - [Download Python](https://www.python.org/downloads/)
   - *Important:* Ensure you check the box **"Add Python to PATH"** during installation.
## 🤖 Step 1: Create a Discord Bot

To get the bot running, you need a Discord Bot Token from the Discord Developer Portal:

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications).
2. Click **New Application** in the top right corner. Give it a name (e.g., `MercariBuddy`) and agree to the terms.
3. In the left sidebar, click **Bot**.
4. Click **Add Bot** and confirm.
5. Under the bot username, click **Reset Token** and copy the generated token. **Keep this token secret!** You will need it for your `.env` file.
6. Scroll down on the Bot page to the **Privileged Gateway Intents** section:
   - Enable **Message Content Intent** (required so the bot can read commands starting with `!`).
   - Enable **Presence Intent** (optional, but good to have).
   - Click **Save Changes**.

---

## 🔗 Step 2: Invite the Bot to Your Server

1. In the Developer Portal, go to **OAuth2** -> **URL Generator** in the left sidebar.
2. Under **Scopes**, select `bot`.
3. Under **Bot Permissions**, select the following:
   - `Send Messages`
   - `Embed Links`
   - `Read Message History`
4. Copy the URL generated at the bottom of the page.
5. Paste this URL into your web browser, choose your Discord server, and click **Authorize**.

---

## ⚙️ Step 3: Run the Setup Script

1. Double-click the `setup.bat` file in the project folder.
2. The setup script will automatically:
   - Create a Python virtual environment (`venv`) to keep your system clean.
   - Upgrade pip and install all required libraries (including the modern `discord.py` and cryptographic libraries).
   - Generate a default `.env` configuration file.
3. Press any key to close the window once the setup is finished.

---

## 📝 Step 4: Configure the Bot

1. Open the newly created `.env` file in a text editor (like Notepad).
2. Set your **DISCORD_TOKEN** inside the quotes:
   ```env
   DISCORD_TOKEN="YOUR_BOT_TOKEN_HERE"
   ```
3. **Database Configuration**:
   - By default, `DB_TYPE="sqlite"` is set. The bot will automatically create and use a local file database named `mercaribuddy.db` in your project folder. No additional configuration is required!
   - *(Optional)* If you prefer to use PostgreSQL, set `DB_TYPE="postgres"` and fill in the `USERNAME`, `DATABASE`, `PASSWORD`, `HOST`, and `PORT` fields.

---

## 🚀 Step 5: Start the Bot

1. Double-click `run.bat`.
2. A command prompt window will open, activate the virtual environment, and boot the bot.
3. You should see messages confirming it connects to the SQLite database and outputting:
   ```text
   Connecting to SQLite database: ...
   MercariBuddy#XXXX has connected to Discord!
   ```
4. Keep the command prompt window open. Closing it will stop the bot.

---

## 💬 How to Use the Bot

> [!NOTE]
> The bot's commands are designed to work in **Direct Messages (DMs)** only to keep channel chat clean. Direct Message your bot to use the commands below.

### Commands

*   `!help` - Display the help menu.
*   `!add [search term]` - Register a keyword you want to track (e.g. `!add My Melody`). The bot will scan Mercari every 30 seconds and send you a direct message with an embed whenever a new listing matches this term.
*   `!list` - Display all of your currently tracked keywords and the number of listings found for each.
*   `!delete [search term]` - Stop tracking a specific keyword (e.g. `!delete My Melody`).
*   `!deleteall` - Stop tracking all of your keywords and delete them from the database.

### 🔘 Buyee & Mercari Buttons
When a new listing is found, the bot sends an embed containing the item name, price, condition, and image. At the bottom of the embed, you will see two buttons:
1. **View on Mercari Japan**: Opens the original listing on jp.mercari.com.
2. **View on Buyee**: Opens the listing directly through the Buyee proxy service for easy checkout.
