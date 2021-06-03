from bot import bot

def loadingFixed(func):
    def inner(call):
        bot.answer_callback_query(call.id)
        return func(call)
    return inner