# Telegram Advertise Sender Bot

A powerful and flexible Telegram bot built with Python and the Telethon library. This bot allows you to automate sending scheduled messages to Telegram groups or users using an Excel file for schedule and message configuration.

---

## Features

- **Excel-based Configuration**:
  - Upload an Excel file with schedule and message details.
  - Automatically processes the file and plans message delivery.

- **Flexible Scheduling**:
  - Supports daily or weekly schedules for specific times.
  - Enables targeting specific groups or users.

- **Dynamic Group Management**:
  - Automatically joins groups if not already a member.
  - Validates participation status before sending messages.

- **Real-time Monitoring**:
  - Reacts to file uploads or commands from specific authorized users.

- **Customizable Settings**:
  - Define control users, schedules, and bot behaviors through a `.env` file.

- **Robust Logging**:
  - Provides detailed logs for errors and critical actions.

---

## Requirements

- Python 3.8 or newer

### Python libraries:
- Telethon
- Pandas
- OpenPyXL
- dotenv
- schedule

_will be installed via pip install -r requirements.txt_

---

## Installation

1. **Clone the Repository**:
```bash
git clone https://github.com/your-username/telegram-advertise-sender.git
cd telegram-advertise-sender 
```

2. Create a Virtual Environment:

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```
3. Install Dependencies:

```bash
pip install -r requirements.txt
```

Create a .env File:

```plaintext
API_ID=<Your Telegram API ID>
API_HASH=<Your Telegram API Hash>
PHONE_NUMBER=<Your Phone Number>
XLS_FILE=<Path to Default Excel File>
CONTROL_USER_ID=<Comma-Separated Telegram User IDs> for recieve new .xls file.
SCHEDULE_CHECK_INTERVAL=<Interval in Seconds> 30 sec ok
```
Prepare the Excel File:

Sheet Schedule: Contains schedule details.

Group	Time to send	Mon	Tue	Wed	Thu	Fri	Sat	Sun
@group_name	10:00:00	1	0	1	0	1	0	1
Sheet Message: Contains a single cell with the message text.

Run the Bot:

```bash
./venv/bin/python bot.py
```
## Usage
Start the Bot:

The bot will automatically log in and start listening for events.
Upload a New Excel File:

Send an Excel file to the bot from an authorized user to update the schedule and message.
Monitor Logs:

Logs provide real-time feedback on the bot’s actions and any errors.
## Project Structure
```bash
.
├── bot.py                 # Main script for the bot
├── requirements.txt       # List of dependencies
├── .env                   # Environment variables
└── README.md              # Project documentation```