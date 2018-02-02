from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, Filters
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import Config
import logging
from dblib import DbLib

#------------- Работа с пользователями
allow_users = []
admin_users = ["Oilnur"]


def add_admin_user(db,users):
    """
        добавление пользователей администратором в БД
    """
    for user in users:
        db.add_user(user,"administartor")
    return True

# проверка на разрешенного пользователя
def is_allow_user(func):
    def wrapped(*args, **kwargs):
        nameuser = args[2].message.from_user.username        
        for user in allow_users:
            if user==nameuser:
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

# --- Подготовительные работы с БД
db = DbLib("db/library.db")
add_admin_user(db,admin_users)
# db.add_user("andrey","user")
allow_users = db.get_all_username()
# --- END Подготовительные работы с БД


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
        self.reg_handler("help",self.about)
        # команды администратора
        self.reg_handler("adduser",self.add_user, True)
        self.reg_handler("lsuser",self.ls_user)
        self.reg_handler("deluser",self.del_user, True)
        # END команды администратора
        # END регистрация команд

    def add_user(self,bot,update,**args):
        args_list=args["args"]
        if not (len(args_list)>0):
            update.message.reply_text("Формат команды: \\adduser имя_пользователя")
            return False
        db.add_user(args_list[0],"user")
        update.message.reply_text("Пользователь {} добавлен в базу.".format(args_list[0]))

    def ls_user(self,bot,update):
        all_user = db.get_all_username()
        str=""
        for s in all_user:
            str=str+s+"\n"
        update.message.reply_text("Список всех пользователей: \n{}".format(str))
    
    def del_user(self,bot,update, **args):
        args_list=args["args"]
        if not (len(args_list)>0):
            update.message.reply_text("Формат команды: \\deluser имя_пользователя")
            return False
        db.del_user(args_list[0])
        self.ls_user(bot, update)
        return True


        

    # обработка получение документов от пользователя (сохранение в указанной папке)
    def get_book_to_lib(self,bot,update):
        file_id = update.message.document.file_id
        filename = update.message.document.file_name
        newFile = bot.get_file(file_id)
        newFile.download('files/savedoc/'+filename)

    def reg_handler(self, command=None,hand=None,pass_args=False):
        """ регистрация команд которые обрабатывает бот """
        if (command is None) or (hand is None):
            return
        self.bot.dispatcher.add_handler(CommandHandler(command, hand,pass_args=pass_args))
        
    def about(self, bot, update):
        """ сообщает какие есть возможности у бота """
        update.message.reply_text("Если вы администратор бота, то вам доступны команды для управления пользователями.")
    

    @is_allow_user
    def start(self, bot, update):
        """
        keyboard = [[InlineKeyboardButton("Help", callback_data="about_bot"),
                 InlineKeyboardButton("Settings", callback_data='settings')],
                [InlineKeyboardButton("Яndex", url='http://ya.ru')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        """
        update.message.reply_text('Добро пожаловать, {}! Я бот который поможет вам вести свою библиотеку и позволит вам читать книги. '.format(update.message.from_user.first_name)) #, reply_markup=reply_markup)
        

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