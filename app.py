from telebot import TeleBot, apihelper, types
from flask import Flask, request
from models import Models
from bot import bot, URL
from decorators import loadingFixed

server = Flask(__name__)
models = Models(server)

IN_INPUT_TOKEN = []
IN_INPUT_START_MESSAGE = {}

@bot.message_handler(commands = ['start'])
def start(message):
    text = '''
@FeedbotgramBot is a simple bot for create feedback bot.

Bot commands:

/addbot - connect a new bot
/mybots - manage bots
    '''
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('Source code this bot', url = 'https://github.com/salismazaya/feedback-telegram-bot'))
    bot.send_message(message.chat.id, text, reply_markup = markup)


@bot.message_handler(commands = ['addbot'])
def addBot(message):
    text =  '''
Send bot token for connect!

/cancel for cancel this operation
'''
    if not message.from_user.id in IN_INPUT_TOKEN:
        IN_INPUT_TOKEN.append(message.from_user.id)
    bot.send_message(message.chat.id, text)


@bot.message_handler(commands = ["cancel"])
def cancel(message):
    try:
        lists = [IN_INPUT_TOKEN, IN_INPUT_START_MESSAGE]
        for x in lists:
            if isinstance(x, list):
                if message.from_user.id in x:
                    x.remove(message.from_user.id)

            elif isinstance(x, dict):
                if x.get(message.from_user.id):
                    del x[message.from_user.id]
        
        bot.send_message(message.chat.id, 'Ok!')
    except Exception as e:
        print(e)


@bot.message_handler(func = lambda msg: msg.from_user.id in IN_INPUT_TOKEN)
def addBotProcess(message):
    client = TeleBot(message.text)
    try:
        client.remove_webhook()
        me = client.get_me()
        data = models.Bot.query.filter_by(id = me.id).first()
        if data:
            if data.owner == message.from_user.id:
                bot.send_message(message.chat.id, 'Bot has connected!')
                return
            else:
                bot.send_message(message.chat.id, 'Bot has connected to another user!')
                return

        client.set_webhook(URL + '/webhook/' + client.token)
        botData = models.Bot(id = me.id, owner = message.from_user.id,
                            username = me.username, token = client.token,
                            start_message = 'This bot made by @FeedbotgramBot')
        models.db.session.add(botData)
        models.db.session.commit()
        bot.send_message(message.chat.id, 'Succes to connect bot @' + me.username)
        if message.from_user.id in IN_INPUT_TOKEN:
            IN_INPUT_TOKEN.remove(message.from_user.id)
    except apihelper.ApiTelegramException:
        bot.send_message(message.chat.id, 'Token api not valid!')


@bot.message_handler(commands = ['mybots'])
def mybots(message):
    data = models.Bot.query.filter_by(owner = message.from_user.id).all()
    if not data:
        bot.send_message(message.chat.id, 'No bot found!')
        return
        
    markup = types.InlineKeyboardMarkup()
    text = 'Select bot'
    for x in data:
        markup.row(types.InlineKeyboardButton(x.username, callback_data = 'manage_bot|' + x.username))
        
    bot.send_message(message.from_user.id, text, reply_markup = markup)


@bot.callback_query_handler(func = lambda call: call.data.startswith('manage_bot|'))
@loadingFixed
def manageBot(call):
    username = call.data.split('|')[-1]
    data = models.Bot.query.filter_by(username = username).first()
    if not data:
        bot.answer_callback_query(call.id, text = 'Bot not found!')
        return
        
    if call.from_user.id != data.owner:
        bot.answer_callback_query(call.id, text = 'Forbidden!')
        return

    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton('Edit Start Message', callback_data = 'edit_start_message|' + username))
    markup.row(types.InlineKeyboardButton('Reconnect', callback_data = 'reconnect|' + username),
                types.InlineKeyboardButton('Delete', callback_data = 'delete|' + username)
                )
    markup.row(types.InlineKeyboardButton('Back', callback_data = 'back_to_select_bot'))
    bot.edit_message_text('Selected @' + username, chat_id = call.message.chat.id, message_id = call.message.id, reply_markup = markup)


@bot.callback_query_handler(func = lambda call: call.data == 'back_to_select_bot')
@loadingFixed
def backToSelectBot(call):
    data = models.Bot.query.filter_by(owner = call.from_user.id).all()
    if not data:
        bot.send_message(call.message.chat.id, 'No bot found!')
        return
        
    markup = types.InlineKeyboardMarkup()
    text = 'Select bot'
    for x in data:
        markup.row(types.InlineKeyboardButton(x.username, callback_data = 'manage_bot|' + x.username))
    bot.edit_message_text(text, chat_id = call.message.chat.id, message_id = call.message.id, reply_markup = markup)


@bot.callback_query_handler(func = lambda call: call.data.startswith('reconnect|'))
def reconnect(call):
    username = call.data.split('|')[-1]
    data = models.Bot.query.filter_by(username = username).first()
    if not data:
        bot.answer_callback_query(call.id, text = 'Bot not found!')
        return
        
    if call.from_user.id != data.owner:
        bot.answer_callback_query(call.id, text = 'Forbidden!')
        return

    try:
        client  = TeleBot(data.token)
        client.remove_webhook()
        client.set_webhook(URL + '/webhook/' + data.token)
        bot.answer_callback_query(call.id, text = 'Success!')
    except apihelper.ApiTelegramException:
        bot.answer_callback_query(call.id, text = 'Token api not valid!')


@bot.callback_query_handler(func = lambda call: call.data.startswith('edit_start_message|'))
@loadingFixed
def editStartMessage(call):
    username = call.data.split('|')[-1]
    data = models.Bot.query.filter_by(username = username).first()
    if not data or call.from_user.id != data.owner:
        return
    
    IN_INPUT_START_MESSAGE[call.from_user.id] = username
    bot.send_message(call.message.chat.id, 'Send new start message!')
    bot.send_message(call.message.chat.id, f'''
Current start message:

{data.start_message}
    ''' )

@bot.message_handler(func = lambda msg: IN_INPUT_START_MESSAGE.get(msg.from_user.id))
def editStartMessageProcess(message):
    username = IN_INPUT_START_MESSAGE[message.from_user.id]
    data = models.Bot.query.filter_by(username = username).first()
    if not data:
        bot.send_message(message.chat.id, 'Bot not found!')
        return
        
    if message.from_user.id != data.owner:
        bot.send_message(message.chat.id, 'Forbidden!')
        return

    data.start_message = message.text
    models.db.session.commit()

    if IN_INPUT_START_MESSAGE.get(message.from_user.id):
        del IN_INPUT_START_MESSAGE[message.from_user.id]
    
    bot.send_message(message.chat.id, 'Success!')

@bot.callback_query_handler(func = lambda call: call.data.startswith('delete|'))
def deleteBot(call):
    username = call.data.split('|')[-1]
    data = models.Bot.query.filter_by(username = username).first()
    if not data:
        bot.answer_callback_query(call.id, text = 'Bot not found!')
        return
        
    if call.from_user.id != data.owner:
        bot.answer_callback_query(call.id, text = 'Forbidden!')
        return
    
    models.db.session.delete(data)
    models.db.session.commit()

    try:
        client = TeleBot(data.token)
        client.remove_webhook()
        bot.answer_callback_query(call.id, text = 'Successfully deleted!')
        bot.edit_message_text('Bot deleted', chat_id = call.message.chat.id, message_id = call.message.id)
    except apihelper.ApiTelegramException:
        bot.answer_callback_query(call.id)


@server.route('/')
def setWebhook():
    bot.remove_webhook()
    bot.set_webhook(URL + bot.token)
    return '!'


@server.route('/' + bot.token, methods = ['POST'])
def getMessage():
    json_string = request.get_data().decode()
    update = types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return '!'


@server.route('/webhook/<token>', methods = ['POST'])
def clientGetMessage(token):
    try:
        json_string = request.get_data().decode()
        messsage = types.Update.de_json(json_string).message
        if messsage.chat.type != 'private':
            return '!'

        client = TeleBot(token)
        data = models.Bot.query.filter_by(id = client.get_me().id).first()

        if messsage.text == '/start':
            client.send_message(messsage.chat.id, data.start_message)
            return '!'

        if data.owner != messsage.from_user.id:
            client.forward_message(data.owner, messsage.chat.id, messsage.id)
        else:
            if not getattr(messsage, 'reply_to_message') or not messsage.reply_to_message.forward_from:
                client.forward_message(data.owner, messsage.chat.id, messsage.id)
            else:
                target = messsage.reply_to_message.forward_from.id
                client.copy_message(target, messsage.chat.id, messsage.id)

        return '!'
    except:
        return '!'

if __name__ == '__main__':
    server.run(debug = True)
