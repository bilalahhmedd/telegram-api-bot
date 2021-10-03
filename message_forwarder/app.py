from telethon import TelegramClient, events
#import settings
#---- LOGGING
import logging
logging.basicConfig(format = "[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s",
                   level = logging.WARNING)
#---- LOGGING

import tkinter as tk
import threading
import asyncio

#global api_id, api_hash, input_channel, output_channel

# API_ID and API_HASH. Don't edit this, or the userbot won't work!
API_ID = 1521784
API_HASH = "ab30c76a3dfba42d9fe78df2597d4c7a"

# Channels to copy and output to
INPUT  = "test" # The target. The userbot will copy any message that's sent here.
OUTPUT = "test" # The output. The userbot will output everything that's copied here.


api_id = API_ID
api_hash = API_HASH
input_channel = INPUT
output_channel = OUTPUT


    

def app():
    client = TelegramClient("listener", api_id, api_hash)
    print("client created **************************************")
    print("api_id: %d \n" %api_id)
    print("api_hash: %s \n" %api_hash)
    print("input channel: %s \n" %input_channel)
    print("output channel: %s \n" %output_channel)
    client.parse_mode = "md"
    @client.on(events.NewMessage(chats = input_channel))
    async def forward(event):
        text_message = event.message
        if text_message.text.startswith("SELL") or text_message.text.startswith("BUY"):
            message = event.message.text.split()
            caption = f"{message[0]} {message[1]} @ {message[3]}\n{message[4]} {message[5]}\n{message[6]} {message[7]}"
            await event.reply(caption)
        elif text_message.text.startswith("SIGNAL:"):
            message = event.message.text.split()
            caption = f"{message[1]} {message[2]} @ {message[4]}\n{message[5]} {message[6]}\n{message[11]} {message[12]}"
            await event.reply(caption)
        elif text_message.text.startswith("**"):
            message = event.message.text.split()
            caption = f"{message[1]} {message[0].replace('**', '')} @ {message[3].replace('Price:', '')}\nSL: {message[4].replace('Stop:', '')}\nTP: {message[5].replace('TP:', '')}"
            await event.reply(caption)

    client.start()
    print("Userbot on!")
    client.run_until_disconnected()



loop = asyncio.get_event_loop()
# let's create gui here
# define loop which can be used later
def start_app():
    asyncio.set_event_loop(loop)
    app()


# define window components here

t = threading.Thread(target=start_app)




window = tk.Tk()
window.geometry("400x300")
window.title("Message Forwarder Screen")
#api_id widgets
l_id = tk.Label(window, text="enter api_id: ")
txt_id = tk.Entry()
    
#api_hash widgets 
l_hash = tk.Label(window, text="enter api_hash: ")
txt_hash = tk.Entry()
    
#input channel widgets
l_input_channel = tk.Label(window, text="enter input channel: ")
txt_input_channel = tk.Entry()
#output channel widgets
l_output_channel = tk.Label(window, text="enter output_channel: ")
txt_output_channel = tk.Entry()

def submit():
        global api_id, api_hash, input_channel, output_channel
        api_id = int(txt_id.get())
        api_hash = txt_hash.get()
        input_channel = txt_input_channel.get()
        output_channel = txt_output_channel.get()
        '''
        print("api_id: %d \n" %api_id)
        print("api_hash: %s \n" %api_hash)
        print("input_channel: %s \n" %input_channel)
        print("output_channel %s \n" %output_channel)
        '''
        t.start()


# buttons widgets
data_submit = tk.Button(window,text="submit and start app",bg="green",command=submit)
    
app_start = tk.Button(window,text="Start App with default values",bg="green",command=t.start)
#app_stop = tk.Button(window,text="       Stop App       ",bg="red",command=stop) 
#app_stop.grid(column=10,row=0)	
def gui():
    
    l_id.grid(row=0,column=1)
    txt_id.grid(row=0,column=2)
    l_hash.grid(row=1,column=1)
    txt_hash.grid(row=1,column=2)
    l_input_channel.grid(row=2,column=1)
    txt_input_channel.grid(row=2,column=2)
    l_output_channel.grid(row=3,column=1)
    txt_output_channel.grid(row=3,column=2)
    data_submit.grid(row=4,column=1)
    app_start.grid(row=5,column=1)	

    window.mainloop()











#*************************** execute code here
gui()

