#!./venv/bin/python

from telethon import TelegramClient, events
from telethon.tl.types import User, Chat
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import GetDialogsRequest
from dotenv import dotenv_values
import pandas as pd
import schedule
import logging
import os
import sys
import asyncio

# Настройка логирования
# logging.basicConfig(level=logging.INFO)
logging.basicConfig(level=logging.WARNING)

# Загружаем переменные окружения из .env файла в словарь
config = dotenv_values(".env")

# Загружаем значения из словаря
api_id = config.get('API_ID')
api_hash = config.get('API_HASH')
phone_number = config.get('PHONE_NUMBER')
xls_file = config.get('XLS_FILE')
# xls_file = 'advertize-sender.xlsx'
# ID пользователя, от которого нужно фильтровать сообщения
# control_user_id = int(config.get('CONTROL_USER_ID'))
control_user_ids = [int(user_id) for user_id in config.get('CONTROL_USER_ID', '').split(',')]

schedule_check_interval = int(config.get('SCHEDULE_CHECK_INTERVAL'))

# print(f'{control_user_id=}')
# Create the client and connect
client = TelegramClient('advertise-sender', api_id, api_hash)

@client.on(events.NewMessage(from_users=control_user_ids))
# @client.on(events.NewMessage())
async def handle_new_message(event):
    sender = await event.get_sender()
    chat = await event.get_chat()

    logging.info(f"Message from {sender.first_name} {sender.last_name} (@{sender.username}):")
    # logging.info(f"Chat: {chat.title if hasattr(chat, 'title') else 'Private Chat'}")

    # Проверяем, является ли сообщение файлом
    if event.message.document:
        document = event.message.document
        file_name = document.attributes[0].file_name
        file_extension = os.path.splitext(file_name)[1].lower()

        # Проверяем, является ли файл Excel
        if file_extension in ['.xlsx', '.xls']:
            logging.info(f"Received Excel file: {file_name}")
            # Скачиваем файл и сохраняем его под заданным именем
            file_path = await client.download_media(document, file=xls_file)
            logging.info(f"File downloaded to: {file_path}")

            # Загрузка расписания и сообщения
            schedule_df = load_schedule(file_path)
            adv_message = load_message(file_path)

            if schedule_df is None or adv_message is None:
                logging.critical("Failed to load schedule or message. Stopping the bot.")
                await event.reply('🛑 Ошибка при обработке файла эксель.\n'
                                  'Новый файл не принят, все работает по старому.')
                return

            # Отмена всех запланированных задач
            schedule.clear()
            await event.reply('🟡 Старое расписание очищено.')

            # Планирование новых сообщений
            schedule_load_report = schedule_messages(schedule_df, adv_message)

            num_jobs = len(schedule.jobs)

            await event.reply(f'🟢 Новое расписание загружено.\n'
                              f'Прочитано строк из файла: {len(schedule_df)}\n'
                              f'Запланировано задач: {num_jobs}')
            await event.reply(f'{schedule_load_report}')

            logging.info('Schedule updated with new Excel file.')
        else:
            logging.info(f"Received non-Excel file: {file_name}")
    else:
        logging.info(f"Message: {event.message.text}")
        # logging.info("-" * 40)

    # Example: Reply to the message
    # if event.message.text.lower() == 'hello':
    #     await event.reply('Hello! How can I help you?')


async def check_and_join_chat(chat_username):
    # Получаем информацию о чате
    chat = await client.get_entity(chat_username)

    # Проверяем, состоим ли мы в чате
    participants = await client.get_participants(chat)
    user_id = (await client.get_me()).id
    is_member = any(participant.id == user_id for participant in participants)

    if not is_member:
        # Если не состоим в чате, вступаем в него
        await client(JoinChannelRequest(chat))
        logging.warning(f"Вступили в чат {chat_username}")
    else:
        logging.info(f"Уже состоим в чате {chat_username}")


async def send_message(group_name, message):
    try:
        # Проверяем, что бот является участником чата
        # chat = await client.get_entity(group_name)
        # if isinstance(chat, User):
        #     await client.send_message(group_name, message)
        #     logging.info(f"Sent message to user: {group_name}")
        #     return
        # else:
        #     logging.info(f"{chat.username} is not User")
        await check_and_join_chat(group_name)
        await client.send_message(group_name, message)
        logging.warning(f"Message sent to {group_name}!")
    except Exception as e:
        logging.error(f"Error while sending message to {group_name}: {e}")

def load_schedule(file_path):
    try:
        schedule_df = pd.read_excel(file_path, sheet_name='Schedule')
        schedule_df = schedule_df.fillna(0)
        # print(schedule_df)
        schedule_df['Time to send'] = pd.to_datetime(schedule_df['Time to send'], format='%H:%M:%S', errors='coerce').dt.time
        return schedule_df
    except Exception as e:
        logging.error(f'Error loading schedule from excel file: {e}')
        return None

def load_message(file_path):
    try:
        message_df = pd.read_excel(file_path, sheet_name='Message', header=None)
        message = message_df.iloc[0, 0]
        short_message = message[:10].replace("\n", " ")
        logging.info(f'Loaded adv message: {short_message}...')
        return message
    except Exception as e:
        logging.error(f'Error loading advertise message from excel file: {e}')
        return None

def schedule_messages(schedule_df, adv_message):
    # print(schedule_df)
    report = ''
    for _, row in schedule_df.iterrows():
        group_name = row['Group']
        send_time = row['Time to send'].strftime('%H:%M')
        # print(f'{row=}')
        if row['Mon'] == 1:
            schedule.every().monday.at(send_time).do(
                lambda group_name=group_name, adv_message=adv_message: 
                    asyncio.run_coroutine_threadsafe(send_message(group_name, adv_message), client.loop)
            )
            logging.info(f"{group_name} planned at {send_time} on Mon")
            report += f"{group_name} at {send_time} on Mon\n"
        if row['Tue'] == 1:
            schedule.every().tuesday.at(send_time).do(
                lambda group_name=group_name, adv_message=adv_message: 
                    asyncio.run_coroutine_threadsafe(send_message(group_name, adv_message), client.loop)
            )
            logging.info(f"{group_name} planned at {send_time} on Tue")
            report += f"{group_name} at {send_time} on Tue\n"
        if row['Wed'] == 1:
            schedule.every().wednesday.at(send_time).do(
                lambda group_name=group_name, adv_message=adv_message: 
                    asyncio.run_coroutine_threadsafe(send_message(group_name, adv_message), client.loop)
            )
            logging.info(f"{group_name} planned at {send_time} on Wed")
            report += f"{group_name} at {send_time} on Wed\n"            
        if row['Thu'] == 1:
            schedule.every().thursday.at(send_time).do(
                lambda group_name=group_name, adv_message=adv_message: 
                    asyncio.run_coroutine_threadsafe(send_message(group_name, adv_message), client.loop)
            )
            logging.info(f"{group_name} planned at {send_time} on Thu")
            report += f"{group_name} at {send_time} on Thu\n"            
        if row['Fri'] == 1:
            schedule.every().friday.at(send_time).do(
                lambda group_name=group_name, adv_message=adv_message: 
                    asyncio.run_coroutine_threadsafe(send_message(group_name, adv_message), client.loop)
            )
            logging.info(f"{group_name} planned at {send_time} on Fri")
            report += f"{group_name} at {send_time} on Fri\n"            
        if row['Sat'] == 1:
            schedule.every().saturday.at(send_time).do(
                lambda group_name=group_name, adv_message=adv_message: 
                    asyncio.run_coroutine_threadsafe(send_message(group_name, adv_message), client.loop)
            )
            logging.info(f"{group_name} planned at {send_time} on Sat")
            report += f"{group_name} at {send_time} on Sat\n"            
        if row['Sun'] == 1:
            schedule.every().sunday.at(send_time).do(
                lambda group_name=group_name, adv_message=adv_message: 
                    asyncio.run_coroutine_threadsafe(send_message(group_name, adv_message), client.loop)
            )
            logging.info(f"{group_name} planned at {send_time} on Sun")
            report += f"{group_name} at {send_time} on Sun\n"            
            
        # schedule.every().day.at(send_time).do(
        #     lambda group_name=group_name, adv_message=adv_message: 
        #         asyncio.run_coroutine_threadsafe(send_message(group_name, adv_message), client.loop)
        # )
        # logging.info(f"{group_name} запланирована на {send_time}")
        
    return report

async def run_scheduler():
    while True:
        schedule.run_pending()
        await asyncio.sleep(schedule_check_interval)

# Основной запуск
async def main():
    # Авторизация через Telegram
    await client.start(phone=phone_number)

    # Загрузка расписания из Excel
    schedule_df = load_schedule(xls_file)
    adv_message = load_message(xls_file)

    # Планирование сообщений
    schedule_load_report = schedule_messages(schedule_df, adv_message=adv_message)

    logging.info('Schedule loaded and activated, waiting for right time.')
    
    # Запуск клиента и обработка событий
    await asyncio.gather(client.run_until_disconnected(), run_scheduler())

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logging.critical(f"Critical error: {e}")
        sys.exit(1)  # Завершает выполнение программы с кодом ошибки 1
