import asyncio
import telebot
from telebot.async_telebot import AsyncTeleBot
import EdgeGPT
import local_secrets

TOKEN = local_secrets.BOT_TOKEN

bot = AsyncTeleBot(TOKEN)
sydney = EdgeGPT.Chatbot('cookie.json')

oc = False

def editRef(msg: str, j: dict):
    try:
        n = msg
        card = j['item']['messages'][1]['adaptiveCards'][0]['body'][0]['text']
        ref = [each[each.find('http'):each.find('"')].strip() for each in card[:card.find('\n\n')].split('\n')]
        for i in range(100):
            if n.find(f'^{i}^') != -1:
                n = n.replace(f'[^{i}^]', f'[({i})]({ref[i-1]})')
    except Exception as e:
        print(f'Error: {e}')
    return n

def prompt(r: dict) -> str:
    p = ''
    for i, each in enumerate(r['item']['messages'][1]['suggestedResponses']):
        p += f'  {i+1}. `{each["text"]}`\n'
    return p

def markup(r: dict, m: telebot.types.Message) -> telebot.types.InlineKeyboardMarkup:
    u = telebot.types.InlineKeyboardMarkup()
    l = []
    for i, each in enumerate(r['item']['messages'][1]['suggestedResponses']):
        if len(each['text'].encode('utf8')) >= 60:
            l = [telebot.types.InlineKeyboardButton('Response not parsed', url='https://t.me/arielsydneybot')]
            break
        l.append(telebot.types.InlineKeyboardButton(str(i+1), callback_data=each['text']))
    if m.text.startswith('/chat '):
        t = m.text[m.text.find('/chat ')+6:].strip()
    else:
        t = m.text.strip()
    l.append(telebot.types.InlineKeyboardButton('Regenerate response', callback_data=t+' $$'))
    u.add(*l)
    return u

def regenMarkup(t: str) -> telebot.types.InlineKeyboardMarkup:
    u = telebot.types.InlineKeyboardMarkup()
    u.add(telebot.types.InlineKeyboardButton('Regenerate response', callback_data=t+' $$'))
    return u

@bot.message_handler()
async def reply(message: telebot.types.Message) -> int:
    global oc
    try:
        if oc:
            await bot.reply_to(message, 'Sorry, I can only process one message at a time, otherwise the account of Ariel would be suspended.')
        else:
            oc = True
            if message.text.split(' ', 1)[0].startswith('/'):
                l = message.text.split(' ', 1)
                if len(l) == 1:
                    cmd = l[0]
                    arg = ''
                else:
                    cmd, arg = l
                if cmd == '/chat':
                    if arg.strip() == '':
                        await bot.reply_to(message, "Hello, I'm here! Please say something like this:\n  <code>/chat Who is Ariel?</code>", parse_mode='html')
                    else:
                        s = await bot.reply_to(message, '*Processing...* \nIt may take a while.', parse_mode='Markdown')
                        r = await sydney.ask(prompt=arg)
                        m = markup(r, s)
                        p = prompt(r)
                        await bot.edit_message_text(editRef(r['item']['messages'][1]['text'].replace('**', '*'), r) + '\n\n*You may ask...* \n' + p, s.chat.id, s.message_id, reply_markup=m, parse_mode='Markdown')
                elif cmd == '/start':
                    await bot.reply_to(message, "Hello, I am Ariel Sydney, a LLM optimised for searching! Use /chat to start chatting.")
            else:
                arg = message.text
                if arg.strip() == '':
                    await bot.reply_to(message, "Hello, I'm here! Please say something like this:\n  <code>/chat Who is Ariel?</code>", parse_mode='html')
                else:
                    s = await bot.reply_to(message, '*Processing...* \nIt may take a while.', parse_mode='Markdown')
                    r = await sydney.ask(prompt=arg)
                    m = markup(r, s)
                    p = prompt(r)
                    await bot.edit_message_text(editRef(r['item']['messages'][1]['text'].replace('**', '*'), r) + '\n\n*You may ask...* \n' + p, s.chat.id, s.message_id, reply_markup=m, parse_mode='Markdown')
            oc = False
    except Exception as e:
        oc = False
        print(f'Error: {e}')
        if message.text.startswith('/chat '):
            t = message.text[message.text.find('/chat ')+6:].strip()
        else:
            t = message.text.strip()
        m = regenMarkup(t)
        await bot.reply_to(message, f'I encountered an error while generating a response: \n\n<code>{e}</code>', markup=m, parse_mode='html')

@bot.callback_query_handler(lambda _: True)
async def callbackReply(callback_query: telebot.types.CallbackQuery):
    global oc
    try:
        if oc:
            await bot.reply_to(callback_query.message, 'Sorry, I can only process one message at a time, otherwise the account of Ariel would be suspended.')
        else:
            oc = True
            text = callback_query.data
            if callback_query.data.endswith(' $$'):
                s = await bot.edit_message_text('*Processing...* \nIt may take a while.', callback_query.message.chat.id, callback_query.message.message_id, parse_mode='Markdown')
            else:
                s = await bot.reply_to(callback_query.message, '*Processing...* \nIt may take a while.', parse_mode='Markdown')
            r = await sydney.ask(prompt=text)        
            m = markup(r, s)
            p = prompt(r)
            await bot.edit_message_text(editRef(f'*Query: {text}* \n' + r['item']['messages'][1]['text'].replace('**', '*'), r) + '\n\n*You may ask...* \n' + p, s.chat.id, s.message_id, reply_markup=m,  parse_mode='Markdown')
            oc = False
    except Exception as e:
        print(f'Error: {e}')

if __name__ == '__main__':
    asyncio.run(bot.polling(non_stop=True, timeout=180))