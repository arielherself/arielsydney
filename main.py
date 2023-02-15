import asyncio
import telebot
from telebot.async_telebot import AsyncTeleBot
import EdgeGPT
import local_secrets

TOKEN = local_secrets.BOT_TOKEN

bot = AsyncTeleBot(TOKEN)
sydney = EdgeGPT.Chatbot('cookie.json')

def removeRef(msg: str):
    ...

def markup(r: dict, s: telebot.types.Message) -> telebot.types.InlineKeyboardMarkup:
    m = telebot.types.InlineKeyboardMarkup()
    menu = []
    for each in r['item']['messages'][1]['suggestedResponses']:
        try:
            if len(each['text'].encode('utf8')) >= 60:
                t = each['text'].encode('utf8')[:50].decode('utf8', errors='ignore') + '...'
            else:
                t = each['text']
            menu.append(telebot.types.InlineKeyboardButton(t, callback_data=f'{s.message_id} {s.chat.id} {each["text"]}'))
        except Exception as e:
            print(f'Error: {e}')
    m.add(*menu, row_width=1)
    return m

@bot.message_handler()
async def reply(message: telebot.types.Message) -> int:
    try:
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
                    await bot.edit_message_text(r['item']['messages'][1]['text'], s.chat.id, s.message_id, reply_markup=m, parse_mode='Markdown')
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
                await bot.edit_message_text(r['item']['messages'][1]['text'], s.chat.id, s.message_id, reply_markup=m, parse_mode='Markdown')
    except Exception as e:
        print(f'Error: {e}')

@bot.callback_query_handler(lambda _: True)
async def callbackReply(callback_query: telebot.types.CallbackQuery):
    try:
        messageID, chatID, text = callback_query.data.split(' ', 2)
        s = await bot.send_message(chatID, '*Processing...* \nIt may take a while.', parse_mode='Markdown')
        r = await sydney.ask(prompt=text)        
        m = markup(r, s)
        await bot.edit_message_text(f'*Question: {text}* \n' + r['item']['messages'][1]['text'], s.chat.id, s.message_id, reply_markup=m,  parse_mode='Markdown')
    except Exception as e:
        print(f'Error: {e}')

if __name__ == '__main__':
    asyncio.run(bot.polling(non_stop=True, timeout=180))