from telethon import TelegramClient, events, types, utils
from telethon.tl.patched import Message
from telethon.tl.custom.messagebutton import MessageButton
from telethon.tl.types.messages import BotCallbackAnswer
from telethon.tl.functions.account import UpdateStatusRequest

import asyncio
import logging
import tracemalloc
import os
import sqlite3
import re
import threading
import tkinter as tk

#loop = asyncio.get_event_loop()
scriptName = str(os.path.basename(__file__).split(".")[0])
print("Starting", scriptName)
api_id = 6
api_hash = "eb06d4abfb49dc3eeb1aeb98ae0f581e"
app_version = '5.11.0 (1709)'
device_model = 'SM-M205FN'
system_version = 'SDK 29'

tracemalloc.start()
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.WARN)
logger = logging.getLogger(__name__)

client_1 = TelegramClient("client_1_" + scriptName, api_id, api_hash, app_version=app_version,
                          device_model=device_model, system_version=system_version)
dbConnection = sqlite3.connect(f"data_{scriptName}.db", isolation_level=None, check_same_thread=False)

ignore_entities = []

# from_to = {-1001389557656: [-1001409636268, -1001412033708], -1001190739025: [-1001409636268, -1001412033708],
#            -1001277274378: [-1001409636268, -1001412033708]}
from_to = {-1001389557656: [-1001409636268], -1001190739025: [-1001409636268],
           -1001277274378_1: [-1001409636268], -1001223414088: [-1001454406502],
           -1001454800574: [-1001409636268]}
from_to = {}
replaces = {'technicalpipsfx':'forexflow_admin'}
anti_anti_bot = False
replace_username = ""
single_client_mode = True
delete_messages = True




async def read_one_sqlite(sql, *args):
    data = await loop.run_in_executor(None, lambda: dbConnection.cursor().execute(sql, args).fetchone())
    return data


async def read_all_sqlite(sql, *args):
    data = await loop.run_in_executor(None, lambda: dbConnection.cursor().execute(sql, args).fetchall())
    return data
client_1.get_messages()
async def exec_sqlite(sql, *args):
    return await loop.run_in_executor(None, lambda: dbConnection.cursor().execute(sql, args))


class BotMessageBind:
    def __init__(self, in_db_id, from_chat_id, from_chat_msg_id, to_chat_id, to_chat_msg_id):
        self.in_db_id: int = in_db_id
        self.from_chat_id: int = from_chat_id
        self.from_chat_msg_id: int = from_chat_msg_id
        self.to_chat_id: int = to_chat_id
        self.to_chat_msg_id: int = to_chat_msg_id

    async def push_changes(self):
        await exec_sqlite(
            f"UPDATE {scriptName}_messagebind SET `from_chat_id` = ?, `from_chat_msg_id` = ?, `to_chat_id` = ?, "
            "`to_chat_msg_id` = ? WHERE in_db_id = ?",
            self.from_chat_id, self.from_chat_msg_id, self.to_chat_id, self.to_chat_msg_id, self.in_db_id)


async def get_message_bind(in_db_id: int):
    res = await read_one_sqlite(f"SELECT * FROM {scriptName}_messagebind WHERE in_db_id = ?", in_db_id)
    if res is None:
        return None
    else:
        return BotMessageBind(*res)


async def get_message_bind_msg_id(from_chat_id: int, from_chat_msg_id: int, to_chat_id: int) -> [int, None]:
    res = await read_one_sqlite(
        f"SELECT to_chat_msg_id FROM {scriptName}_messagebind WHERE from_chat_id = ? and "
        f"from_chat_msg_id = ? and to_chat_id = ?", from_chat_id, from_chat_msg_id, to_chat_id)
    if res is None:
        return None
    else:
        return res[0]


async def create_message_bind(from_chat_id: int, from_chat_msg_id: int, to_chat_id: int, to_chat_msg_id: int):
    await exec_sqlite(
        f"INSERT INTO {scriptName}_messagebind (from_chat_id, from_chat_msg_id, to_chat_id, to_chat_msg_id) VALUES "
        f"(?, ?, ?, ?)", from_chat_id, from_chat_msg_id, to_chat_id, to_chat_msg_id)


class ProcessedMessage:
    def __init__(self, text, media):
        self.text = text
        self.media = media


async def process_message(message: Message, to_chat: int):
    if ignore_entities and message.entities:
        for entity in message.entities:
            if isinstance(entity, tuple(ignore_entities)):
                return
    if single_client_mode:
        media = message.media if not isinstance(message.media,
                                                (types.MessageMediaWebPage, types.MessageMediaPoll)) else None
    else:
        f_name = await message.download_media()
        media = f_name
    text_to_send = message.text
    if text_to_send:
        for key, value in zip(replaces.keys(), replaces.values()):
            text_to_send = re.sub(key, value, text_to_send, flags=re.IGNORECASE)
    completed = False

    if anti_anti_bot:
        if message.text and len(message.text) < 30 and message.buttons:
            for button_list in message.buttons:
                if completed:
                    break
                for button in button_list:
                    button: MessageButton
                    if isinstance(button.button, types.KeyboardButtonCallback):
                        res: BotCallbackAnswer = await button.click()
                        text_to_send = res.message
                        completed = True
                        break
    lower = text_to_send.lower()
    if any(x in lower for x in ['succes ratio']):
        return False
    if replace_username:
        all_usernames = re.findall(r'@\w+', text_to_send)
        if all_usernames:
            for uname in all_usernames:
                text_to_send = text_to_send.replace(uname, replace_username)
    return ProcessedMessage(text_to_send, media)


@client_1.on(events.MessageDeleted())
async def delete_message_handler(event: events.MessageDeleted.Event):
    if delete_messages:
        if event.chat_id not in from_to:
            return
        for to in from_to[event.chat_id]:
            for deleted_id in event.deleted_ids:
                bound = await get_message_bind_msg_id(event.chat_id, deleted_id, to)
                if bound:
                    await client_1.delete_messages(to, [bound])


@client_1.on(events.MessageEdited())
async def edit_message_handler(event: events.MessageEdited.Event):
    if event.chat_id not in from_to:
        return
    message: Message = event.message
    for to in from_to[event.chat_id]:
        processed = await process_message(message, to)
        if not processed:
            raise events.StopPropagation
        ent = await client_1.get_input_entity(to)
        bound = await get_message_bind_msg_id(message.chat_id, message.id, to)
        if bound:
            await client_1.edit_message(ent, bound, processed.text, file=processed.media)
        if processed.media and not single_client_mode:
            os.remove(processed.media)


@client_1.on(events.Album())
async def album_handler(event: events.Album.Event):
    if event.chat_id not in from_to:
        raise events.StopPropagation
    text = None
    for to in from_to[event.chat_id]:
        files = []
        for i, message in enumerate(event.messages):
            processed = await process_message(message, to)
            if not processed:
                raise events.StopPropagation
            if i == 0:
                text = processed.text
            files.append(processed.media)
        message = event.messages[0]
        ent = await client_1.get_input_entity(to)
        reply_to = None
        if message.reply_to_msg_id:
            reply_to = await get_message_bind_msg_id(event.chat_id, message.reply_to_msg_id, to)
            if not reply_to:
                return
        sent = await client_1.send_file(ent, file=files, caption=text, reply_to=reply_to)
        await create_message_bind(event.chat_id, message.id, to, sent[0].id)
        if not single_client_mode:
            for file in files:
                os.remove(file)
    raise events.StopPropagation


@client_1.on(events.NewMessage(outgoing=True, incoming=True))
async def message_handler(event: events.NewMessage.Event):
    message: Message = event.message
    if not event.is_private:
        print(message.chat_id, message.text.replace("\n", "\\n") if message.text else None)
    if event.chat_id not in from_to:
        return

    if message.grouped_id:
        raise events.StopPropagation
    for to in from_to[event.chat_id]:
        processed = await process_message(message, to)
        if not processed:
            raise events.StopPropagation
        ent = await client_1.get_input_entity(to)
        reply_to = None

        if message.reply_to_msg_id:
            reply_to = await get_message_bind_msg_id(event.chat_id, message.reply_to_msg_id, to)
            if not reply_to:
                return
        await client_1(UpdateStatusRequest(False))

        sent: Message = await client_1.send_message(ent, processed.text, file=processed.media, reply_to=reply_to)
        await client_1(UpdateStatusRequest(True))
        await create_message_bind(event.chat_id, message.id, to, sent.id)
        if processed.media and not single_client_mode:
            os.remove(processed.media)



async def app():
    print('Preparing database...')
    await exec_sqlite(
        f"CREATE TABLE IF NOT EXISTS {scriptName}_messagebind (`in_db_id` INTEGER DEFAULT 0 PRIMARY KEY ,"
        f" `from_chat_id` INTEGER DEFAULT 0, `from_chat_msg_id` INTEGER DEFAULT 0, "
        f"`to_chat_id` INTEGER DEFAULT 0, `to_chat_msg_id` INTEGER DEFAULT 0)")
    print('Starting client_1 (receiver)...')
    await client_1.start()
    client_1_me = await client_1.get_me()
    await client_1.get_dialogs()
    print(f"Authorized client_1 as @{client_1_me.username} ({utils.get_display_name(client_1_me)})")
    print('Started')


async def start_app():
    
        print('starting main app now')
        await asyncio.sleep(1)
        await app()
def loop_in_thread(loop):
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_app())
loop= asyncio.get_event_loop()

t = threading.Thread(target=loop_in_thread, args=(loop,))
#t.start()
#loop= asyncio.get_event_loop()
window = tk.Tk()
window.geometry("650x400")

# define data frame here and bind with data entry widgets
data_frame = tk.Frame(window,relief=tk.RAISED, borderwidth=1,background='lightgray',width=300,height=200)
data_frame.place(x=0,y=0,width=650,height=175)
# label widgets
l_id = tk.Label(data_frame,text='api_id ',anchor='w',width=10)
l_hash = tk.Label(data_frame,text='api hash ',anchor='w',width=10)
#l_hash = tk.Label(window,text='enter api_hash: ')
l_from = tk.Label(data_frame,text='from channel id ',anchor='w',width=10)
l_to = tk.Label(data_frame,text="to channel_id")

# entery widgets
txt_id = tk.Entry(data_frame,width=60)
txt_hash = tk.Entry(data_frame,width=60)
txt_from = tk.Entry(data_frame,width=60)
txt_to = tk.Entry(data_frame,width=60)
# status widgets
status_var = tk.StringVar()
status_var.set('status: application is off, press start app to run application')

status = 'bot is running \n'
def update_id():
    global api_id
    api_id = txt_id.get()
    txt_id.delete(0,tk.END)

    global status
    status = status + 'api id: '+str(api_id)+'\n'
def update_hash():
    global api_hash
    api_hash = txt_hash.get()
    txt_hash.delete(0,tk.END)
    global status
    status = status + 'api hash: '+str(api_hash)+'\n'
def update_from_to():
    # we update from_to dictionery which will be used for messaging binding
    val = int(txt_from.get())
    txt_from.delete(0,tk.END)
    val1 = int(txt_to.get())
    txt_to.delete(0,tk.END)
    # bind from chanel with to channel for communication 
    from_to[val]= [val1]
    '''
    # create from_to_status string
    from_to_status = ' '
    for i in from_to:
        from_to_status = from_to_status+'from channel '+str(i)+' >>>> to channel '+ str(from_to[i])+'\n' 
    
    # append to status string
    global status
    status = status + from_to_status
    '''
def print_bindings():
    from_to_status = ' '
    for i in from_to:
        from_to_status = from_to_status+'from channel '+str(i)+' >>>> to channel '+ str(from_to[i])+'\n' 
    
    # append to status string
    global status
    status = status + from_to_status
def start_app_1():
    global status_var
    print_bindings()
    status_var.set(status)
    t.start()

def submit_data():
    update_id()
    update_hash()
    update_from_to()

def stop_app():
    loop.stop()
    status_var.set("Bot stopped now")

    
#button widgets
btn_id = tk.Button(data_frame,text='submit',width=15,command= update_id)
btn_hash = tk.Button(data_frame,text='submit',width=15,command= update_hash)
btn_from_to = tk.Button(data_frame,text='bind channels',width=15,command= update_from_to)
btn_all = tk.Button(data_frame,text='submit all',background='gray',width=15,command=submit_data)




# define control frame here

control_frame = tk.Frame(window,relief=tk.RAISED,borderwidth=1,background='lightgray')
control_frame.pack(fill=tk.X,side=tk.BOTTOM)


#start_button = tk.Button(window, text='start main app', bg='yellow',command = start_app_1)
#stop_button = tk.Button(window, text='stop main app', bg='red',command = loop.stop)

start_button = tk.Button(control_frame, text="START APP",background='green',width=15,command = start_app_1)

stop_button = tk.Button(control_frame, text="STOP APP",background='red',command = loop.stop)
start_button.pack(side=tk.LEFT, padx=5, pady=5)
stop_button.pack(side=tk.RIGHT)

label_frame = tk.LabelFrame(window, text="Application status",width=650,height=200)
label_frame.place(x=0,y=175)


output_label = tk.Label(label_frame,textvariable=status_var)

def main_gui():
    # paint labels on screen
    l_id.grid(column=0,row=0)
    l_hash.grid(column=0,row=1)
    l_from.grid(column=0,row=2)
    l_to.grid(column=0,row=3)
    # paint text boxes on screen
    txt_id.grid(column=1,row=0)
    txt_hash.grid(column=1,row=1)
    txt_from.grid(column=1,row=2)
    txt_to.grid(column=1,row=3)
    # pain buttons on window
    btn_id.grid(column=2,row=0)
    btn_hash.grid(column=2,row=1)
    btn_from_to.grid(column=2,row=3)
    btn_all.place(x=500,y=148)
    output_label.place(x=0,y=0)

    #start_button.grid(column=0,row=10)
    #stop_button.grid(column=0,row=11)

    #status_label.grid(column=0,row=12)
    window.mainloop()
    #stop_button.grid(window,row=11,column=0)
    #await asyncio.gather(client_1.run_until_disconnected(),main_gui())


main_gui()
