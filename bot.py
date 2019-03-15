from functions import *
from settings import PROXY, key_bot
from telegram.ext import CallbackQueryHandler, MessageHandler, Filters, Updater, CommandHandler
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.INFO,
                    handlers=[logging.FileHandler('bot.log', 'a', 'utf-8')]
                    )





def main():
    mybot = Updater(key_bot, request_kwargs=PROXY)
    logging.info('Bot is starting')
    state = {inline: [CallbackQueryHandler(main_menu, pass_user_data=True)],
             "city": [MessageHandler(Filters.text, set_city, pass_user_data=True)],
             'checkin': [MessageHandler(Filters.text, checkin, pass_user_data=True)],
             'checkout': [MessageHandler(Filters.text, checkout, pass_user_data=True)],
             'maxprice': [MessageHandler(Filters.text, max_price, pass_user_data=True)]
             }
    entry_point = [CommandHandler('start', greet_user, pass_user_data=True)]
    search = ConversationHandler(entry_points=entry_point, states=state,
                                 fallbacks=[CommandHandler('start', greet_user, pass_user_data=True)])

    dp = mybot.dispatcher
    dp.add_handler(search)
    mybot.start_polling()
    mybot.idle()


if __name__ == "__main__":
    main()
