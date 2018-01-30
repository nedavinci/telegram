from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, Filters
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import Config
import logging

ABOUT = range(1)

#------------- Работа с пользователями
allow_users = [{"username":"Oilnur"}]

admin_users = [{"username":"Oilnur"}]

# проверка на разрешенного пользователя
def is_allow_user(func):
    def wrapped(*args, **kwargs):
        nameuser = args[2].message.from_user.username        
        for user in allow_users:
            if user["username"]==nameuser:
                return func(*args, **kwargs)
        args[2].message.reply_text(text="Доступ запрещен. Обратитесь к администратору.")
        return False
    return wrapped

# проверка пользователя на то что он является администратором библиотеки
def is_admin_user(func):
    def wrapped(*args, **kwargs):
        nameuser = args[2].message.from_user.username        
        for user in admin_users:
            if user["username"]==nameuser:
                return func(*args, **kwargs)
        args[2].message.reply_text(text="Доступ запрещен. Обратитесь к администратору.")
        return False
    return wrapped
#------------- END Работа с пользователями

class iReadLibTelegramBot:
    def __init__(self, token=None,level_loggining=logging.INFO):
        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            level=level_loggining)
        self.bot = Updater(token)
       
        # обработка добавления книг в библиотеку
        handlerDocument = MessageHandler(filters = Filters.document, callback=self.get_book_to_lib)
        self.bot.dispatcher.add_handler(handlerDocument)

        # регистрация обработчика используя паттерн срабатывания
        self.bot.dispatcher.add_handler(CallbackQueryHandler(self.about,pattern="^about_bot$")) 
        # регистрация обработчика для inline клавиатуры
        self.bot.dispatcher.add_handler(CallbackQueryHandler(self.inlinebutton))   
        # регистрация команд     
        self.reg_handler("start",self.start)
        self.reg_handler("about",self.about)
        self.reg_handler("docs",self.docs)

    # обработка получение документов от пользователя (сохранение в указанной папке)
    def get_book_to_lib(self,bot,update):
        file_id = update.message.document.file_id
        filename = update.message.document.file_name
        newFile = bot.get_file(file_id)
        newFile.download('files/savedoc/'+filename)

    def reg_handler(self, command=None,hand=None):
        """ регистрация команд которые обрабатывает бот """
        if (command is None) or (hand is None):
            return
        self.bot.dispatcher.add_handler(CommandHandler(command, hand))
        

    def about(self, bot, update):
        """ сообщает какие есть возможности у бота """
        update.message.reply_text("Здесь перечислены, то что я умею.")
    

    @is_allow_user
    def start(self, bot, update):
        """   
        sender = update.message.from_user.username
        if not is_allow_user(sender): 
            update.message.reply_text("Доступ запрещен, обратитесь к администратору бота.")   
            return
        """
        keyboard = [[InlineKeyboardButton("Help", callback_data="about_bot"),
                 InlineKeyboardButton("Settings", callback_data='settings')],
                [InlineKeyboardButton("Яndex", url='http://ya.ru')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        update.message.reply_text('Hello {}! I\'m glad to see you! '.format(update.message.from_user.first_name), reply_markup=reply_markup)
        

    def docs(self, bot, update):
        bot.send_message(chat_id=update.message.chat_id, text = "Отправка файла...ждите...")
        bot.send_document(chat_id=update.message.chat_id, document=open('files/1.xlsx', 'rb'))
        

    def inlinebutton(self, bot, update):
        query = update.callback_query
        
        if format(query.data)=="about":
            pass
        else:
            bot.edit_message_text(text="{}".format(query.data),
                                chat_id=query.message.chat_id,
                                message_id=query.message.message_id) 
          
    def run(self):
        """ запуск бота """   
        logging.debug("Start telegram bot")  
        self.bot.start_polling()
        self.bot.idle()


cfg = Config("config.ini")
tgbot = iReadLibTelegramBot(cfg.token,logging.DEBUG)
tgbot.run()