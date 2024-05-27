""" spy.py - credit github.com/Forichok/TelegramOnlineSpy """
from datetime import datetime, timezone
from time import mktime
from asyncio import sleep
from telethon import TelegramClient, events
from telethon.tl.types import UserStatusOnline, UserStatusOffline #
# Required to avoid runtime warnings
import telethon.sync    # pylint: disable=W0611
try:
    import collections.abc as collections
except ImportError:
    import collections

DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'

API_HASH = 'your api hash'
API_ID = 'your api id'
BOT_TOKEN = "your bot token"
USER_NAME = "your user name"

client = TelegramClient(USER_NAME, API_ID, API_HASH)

client.connect()
client.start()
bot = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

data = {}

help_messages = ['/start - start online monitoring ',
         '/stop - stop online monitoring ',
         '/help - show help ',
         '/add - add user to monitoring list "/add +79991234567 UserName"',
         '/list - show added users',
         '/clear - clear user list',
         '/remove - remove user from list with position in list (to show use /list)"/remove 1"',
         '/setdelay - set delay between user check in seconds',
         '/logs - display command log',
         '/clearlogs - clear the command log file',
         '/cleardata - reset configuration',
         '/disconnect - disconnect bot',
         '/getall - status']


class Contact:
    """class Contact:"""
    online = None
    last_offline = None
    last_online = None
    cl_id = ''
    name = ''

    def __init__(self, _id, name):
        self.cl_id = _id
        self.name = name
    def __str__(self):
        return f'{self.name}: {self.cl_id}'
    def status(self):
        """status"""
        if self.online:
            _st="OnLine"
        else:
            _st="-"
            if self.last_online:
                _st+=utc2localtime(self.last_online).strftime("%m-%d %H:%M:%S")
        return f'{self}: {_st}'

@bot.on(events.NewMessage(pattern='^/logs$'))
async def logs(event):
    """Send a message when the command /logs is issued."""
    _str = ''
    with open('spy_log.txt', 'r', encoding="utf-8") as file:
        _str = file.read()
    await event.respond(_str)

@bot.on(events.NewMessage(pattern='/clearlogs$'))
async def clear_logs(event):
    """Send a message when the command /clear_logs is issued."""
    with open('spy_log.txt', 'w', encoding="utf-8") as _f:
        _f.close()
    await event.respond('logs has been deleted')

@bot.on(events.NewMessage(pattern='^/clear$'))
async def clear(event):
    """Send a message when the command /start is issued."""
    message = event.message
    _id = message.chat_id
    data[_id] = {}
    await event.respond('User list has been cleared')

@bot.on(events.NewMessage(pattern='^/help$'))
async def help_(event):
    """async def help_(event):"""
    await event.respond('\n'.join(help_messages))

@bot.on(events.NewMessage())
async def log(event):
    """Send new message to console & spy_log.txt ."""
    message = event.message
    _str=f'{datetime.now(timezone.utc).strftime(DATETIME_FORMAT)}: [{message.chat_id}]: '\
            f'{message.message}'
    print(_str)
    file_name = 'spy_log.txt'
    with open(file_name, 'a', encoding="utf-8") as _f:
        _f.write(_str + '\n')

@bot.on(events.NewMessage(pattern='^/stop$'))
async def stop(event):
    """Send a message when the command /start is issued."""
    message = event.message
    _id = message.chat_id
    if _id not in data:
        data[_id] = {}
    user_data = data[_id]
    user_data['is_running'] = False
    await event.respond('Monitoring has been stopped')

@bot.on(events.NewMessage(pattern='^/cleardata$'))
async def clear_data(event):
    """async def clear_data(event):"""
    data.clear()
    await event.respond('Data has been cleared')

@bot.on(events.NewMessage(pattern='^/start$'))
async def start(event):
    """async def start(event):"""
    message = event.message
    _id = message.chat_id
    if _id not in data:
        data[_id] = {}
    user_data = data[_id]
    if('is_running' in user_data and user_data['is_running']):
        await event.respond('Spy is already started')
        return

    if 'contacts' not in user_data:
        user_data['contacts'] = []

    contacts = user_data['contacts']

    if len(contacts) < 1:
        await event.respond('No contacts added')
        return
    await event.respond('Monitoring has been started')

    counter = 0
    user_data['is_running'] = True

    while True:
        if len(contacts) < 1:
            break
        counter+=1
        print(f'running {_id}: {counter}')
        for contact in contacts:
            account = await client.get_entity(contact.cl_id)
            print(f'{contact.status()}')
            if isinstance(account.status, UserStatusOnline):
                if contact.online is not True:
                    contact.online = True
                    contact.last_offline = datetime.now(timezone.utc)
                    wol='unknown offline time'
                    if contact.last_online is not None:
                        wol = get_interval(contact.last_offline - contact.last_online)
                    await event.respond(f'{wol}> {contact.name} went online.')
            else:
                _user_offline=isinstance(account.status, UserStatusOffline)
                _now = datetime.now(timezone.utc)
                if contact.online is True:
                    contact.online = False
                    contact.last_online = account.status.was_online if _user_offline else _now
                    wol='unknown online time'
                    if contact.last_offline is not None:
                        wol = get_interval(contact.last_online - contact.last_offline)
                    await event.respond(f'{wol}> {contact.name} went offline.' if _user_offline \
                                   else f'DEBUG: {wol}> {contact.name} went undefined=>offline.')
                contact.last_offline = _now
        delay = 5
        if 'delay' in user_data:
            delay = user_data['delay']
        sleep(delay)
    user_data['is_running'] = False
    await event.respond('Spy gonna zzzzzz...')

@bot.on(events.NewMessage(pattern='^/add'))
async def add(event):
    """async def add(event):"""
    message = event.message
    person_info = message.message.split()
    print(person_info)
    phone = person_info[1]
    name = person_info[2]
    _id = message.chat_id
    if _id not in data:
        data[_id] = {}
    user_data = data[_id]

    if 'contacts' not in user_data:
        user_data['contacts'] = []
    contacts = user_data['contacts']
    contact = Contact(phone, name)
    account = await client.get_entity(contact.cl_id)    # phone
    if isinstance(account.status, UserStatusOffline):
        contact.last_online = account.status.was_online
    contacts.append(contact)
    await event.respond(f'{name}: {phone} has been added')


@bot.on(events.NewMessage(pattern='^/remove'))
async def remove(event):
    """async def remove(event):"""
    message = event.message
    person_info = message.message.split()
    print(person_info)
    if len(person_info) < 2:
        await event.respond('Missing index. Show indexes by /list')
        return
    index = int(person_info[1])
    _id = message.chat_id
    if _id not in data:
        data[_id] = {}
    user_data = data[_id]

    if 'contacts' not in user_data:
        user_data['contacts'] = []
    contacts = user_data['contacts']

    if len(contacts) > index:
        del contacts[index]
        await event.respond(f'User №{index} has been deleted')
    else:
        await event.respond('Incorrect index')

@bot.on(events.NewMessage(pattern='^/setdelay'))
async def set_delay(event):
    """async def set_delay(event):"""
    message = event.message
    person_info = message.message.split()
    print(person_info)
    index = int(person_info[1])
    _id = message.chat_id
    if _id not in data:
        data[_id] = {}
    user_data = data[_id]

    print(index)
    if index >= 0:
        user_data['delay'] = index
        await event.respond(f'Delay has been updated to {index}')
    else:
        await event.respond('Incorrect delay')

@bot.on(events.NewMessage(pattern='^/disconnect$'))
async def disconnect(event):
    """async def disconnect(event):"""
    await event.respond('Bot gonna disconnect')
    await bot.disconnect()

def lpad(_ix, _n):
    """lpad(_ix, _n):"""
    __r=f'{_ix}'
    numsp_ml="\N{FIGURE SPACE}\N{FIGURE SPACE}"
    return numsp_ml[:_n-len(__r)]+__r

@bot.on(events.NewMessage(pattern='/list'))
async def list_(event):
    """async def list_(event):"""
    message = event.message
    _id = message.chat_id
    if _id not in data:
        data[_id] = {}
    user_data = data[_id]

    if 'contacts' not in user_data:
        user_data['contacts'] = []
    contacts = user_data['contacts']
    response = 'List is empty'
    ilx=len(contacts)
    numsp="\N{FIGURE SPACE}"
    if ilx:
        response = 'User list: \n'+'\n'.join([f'>{lpad(ix, 2)}:{numsp}{x.status()}' \
                for ix, x in zip(range(ilx),contacts)])
    await event.respond(response)

@bot.on(events.NewMessage(pattern='/getall'))
async def get_all(event):
    """async def get_all(event):"""
    response = ''
    for key, value in data.items():
        response += f'{key}:\n'
        for j, i in value.items():
            if isinstance(i, collections.Sequence):
                response += f'{j}: ' + '\n'.join([str(x) for x in i]) + '\n'
            else:
                response += f'{j}: {i}\n'
        response += '\n'
    await event.respond(response)

def main():
    """Start the bot."""
    print('running')
    bot.run_until_disconnected()

def utc2localtime(utc):
    """utc2localtime(utc):"""
    pivot = mktime(utc.timetuple())
    return utc + (datetime.fromtimestamp(pivot) - datetime.utcfromtimestamp(pivot))

def get_interval(date):
    """get_interval(date):"""
    _d = divmod(date.total_seconds(),86400)  # days
    _h = divmod(_d[1],3600)  # hours
    _m = divmod(_h[1],60)  # minutes # s = _m[1]  # seconds
    _r = f'{int(_d[0])}d ' if _d[0] else ''
    return f'{_r}{int(_h[0]):02d}:{int(_m[0]):02d}:{int(_m[1]):02d}'

if __name__ == '__main__':
    main()
