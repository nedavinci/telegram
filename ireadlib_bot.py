from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, Filters
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import Config
import logging
import os
from dblib import DbLib


#---- сервисные функции

def split_txt_file(filename, kol_slov):
    """
        разбиение txt файла на так называемые страницы, то есть каждая страница вмещает вот такое кол-во строк: kol_slov
        название страниц от 1 до N
    """
    kol_strok = 0
    tek_filename = 1
    buffer = ""
    directory = os.path.dirname(filename)
    with open(filename,"r") as f:
        for line in f:
            if kol_strok == kol_slov:
                with open(directory+"/"+str(tek_filename)+".txt","w") as ff:
                    ff.write(buffer)
                kol_strok = 0
                buffer = ""
                tek_filename = tek_filename + 1
            else:
                buffer = buffer + line
                kol_strok = kol_strok + 1
#---- END сервисные функции


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
            if user==nameuser:
                return func(*args, **kwargs)
        args[2].message.reply_text(text="Доступ запрещен. Обратитесь к администратору.")
        return False
    return wrapped
#------------- END Работа с пользователями

# --- Подготовительные работы с БД
if not os.path.exists("db"):
    os.mkdir("db")
db = DbLib("db/library.db")
add_admin_user(db,admin_users)
# db.add_user("andrey","user")
allow_users = db.get_all_username()
# --- END Подготовительные работы с БД

NAMEBOOK, AUTHORBOOK, BOOK = range(3)

class iReadLibTelegramBot:

    def __init__(self, token=None,level_loggining=logging.INFO):
        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            level=level_loggining)
        self.bot = Updater(token)

        self.newbook = dict()  # промежуточные данные для добавления книги

        # добавление handler диалога на добавление книги в библиотеку
        conv_handler_addbook = ConversationHandler(
            entry_points=[CommandHandler('addbook', self.add_book)],
            states={
                NAMEBOOK: [MessageHandler(Filters.text, self.add_namebook)],
                BOOK: [MessageHandler(Filters.document, self.add_book_document)],
                AUTHORBOOK: [MessageHandler(Filters.text, self.add_author)]
            },
            fallbacks=[CommandHandler('cancel', self.cancel)]
        )
       
        # обработка добавления книг в библиотеку
        #handlerDocument = MessageHandler(filters = Filters.document, callback=self.get_book_to_lib)
        #self.bot.dispatcher.add_handler(handlerDocument)
        # регистрация обработки ошибок
        self.bot.dispatcher.add_error_handler(self.error)
        # регистрация обработчика используя паттерн срабатывания
        self.bot.dispatcher.add_handler(CallbackQueryHandler(self.about,pattern="^about_bot$")) 
        # регистрация обработчика для inline клавиатуры
        self.bot.dispatcher.add_handler(CallbackQueryHandler(self.inlinebutton))   
        # регистрация диалоговых обработчиков
        self.bot.dispatcher.add_handler(conv_handler_addbook)
        # регистрация команд     
        self.reg_handler("start",self.start)
        self.reg_handler("help",self.about)
        # команды администратора
        self.reg_handler("adduser",self.add_user, True)
        self.reg_handler("lsuser",self.ls_user)
        self.reg_handler("deluser",self.del_user, True)
        self.reg_handler("read",self.read_book)
        # END команды администратора
        self.reg_handler("lsbook",self.ls_book)
        # END регистрация команд


    # обработчики диалога addbook
    @is_allow_user
    def add_book(self,bot,update, **args):
        bot.send_message(chat_id=update.message.chat_id, text = "Введите название книги.\n/cancel - отмена операции.")
        return NAMEBOOK
    
    def add_namebook(self,bot,update):
        nameuser = update.message.from_user.username
        namebook = update.message.text  
        book ={"author":"","book": "", "pathbook":"","currentpage":0,"description":""}
        book["book"] = namebook
        self.newbook[nameuser] =  book        
        bot.send_message(chat_id=update.message.chat_id, text = "Введите автора книги.\n/cancel - отмена операции.")
        return AUTHORBOOK
    
    def add_author(self,bot,update):
        nameuser = update.message.from_user.username
        authorbook = update.message.text  
        #book ={"author":"","book": "", "pathbook":"","currentpage":0,"description":""}        
        self.newbook[nameuser]["author"] = authorbook
        bot.send_message(chat_id=update.message.chat_id, text = "Загрузите книгу.\n/cancel - отмена операции.")
        return BOOK
    
    def add_book_document(self,bot,update):
        nameuser = update.message.from_user.username 
        path_lib = "lib"
        path_lib_user = path_lib+"/{0}".format(nameuser)
        path_lib_user_file = path_lib_user+"/{0}-{1}".format(self.newbook[nameuser]["book"],self.newbook[nameuser]["author"])
        path_lib_user_file_full = path_lib_user_file+"/{0}-{1}.txt".format(self.newbook[nameuser]["book"],self.newbook[nameuser]["author"])
        if not os.path.exists(path_lib):
            os.mkdir(path_lib)
        if not os.path.exists(path_lib_user):
            os.mkdir(path_lib_user)
        
        if os.path.exists(path_lib_user_file):
            self.newbook[nameuser]=None
            bot.send_message(chat_id=update.message.chat_id, text = "Название и автор книги существует. Загрузка книги прервана. Попробуйте снова с другим названием.")
            return ConversationHandler.END
        else:
            os.mkdir(path_lib_user_file)

        file_id = update.message.document.file_id
        newFile = bot.get_file(file_id)
        newFile.download(path_lib_user_file_full)

        split_txt_file(path_lib_user_file_full, 20) # разбиваем книгу на страницы по 50 слов
               
        self.newbook[nameuser]["pathbook"] = path_lib_user_file
        db.add_book(nameuser, self.newbook[nameuser])
        self.newbook[nameuser]=None
        bot.send_message(chat_id=update.message.chat_id, text = "Книга загружена.")
        return ConversationHandler.END

    def cancel(self, bot, update):
        # здесь нужно удалить строку в БД, так как отменена задача на добавление книги
        nameuser = update.message.from_user.username
        self.newbook[nameuser]=None
        update.message.reply_text('Вы прервали добавление новой книги.')
        return ConversationHandler.END
    # END обработчики диалога addbook

    # команды работы с книгами
    def ls_book(self, bot, update):
        """
            вывод доступных книг в библиотеке пользователя nameuser, возвращает кол-во книг в библиотеке 
        """
        nameuser = update.message.from_user.username
        books = db.get_all_book(nameuser)
        id_books = []
        if books == []:
            update.message.reply_text('Библиотека пуста.\nМожете добавить книгу командой /addbook')            
        else:
            result=""
            i = 1
            for b in books:
                result = result +str(b[0])+". "+ b[1]+" - "+b[2]+"\n"
                id_books.append(b[0])
                i = i + 1
            update.message.reply_text('Список книг текущего пользователя:\n{0}'.format(result))      
        return id_books

    @is_allow_user
    def read_book(self, bot, update):
        """
            чтение книги
        """
        id_books = self.ls_book(bot, update)
        if len(id_books) == 0:
            update.message.reply_text("Чтение невозможно.")
            return
        keyboard = [[]]
        for id_book in id_books:
            keyboard[0].append(InlineKeyboardButton(str(id_book), callback_data=str(id_book)))
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text('Выберите книгу...', reply_markup=reply_markup)
      
    # END команды работы с книгами

    # обработчики командов администратора
    @is_admin_user
    @is_allow_user    
    def add_user(self,bot,update,**args):
        args_list=args["args"]
        if not (len(args_list)>0):
            update.message.reply_text("Формат команды: \\adduser имя_пользователя")
            return False
        db.add_user(args_list[0],"user")
        update.message.reply_text("Пользователь {} добавлен в базу.".format(args_list[0]))

    @is_admin_user
    @is_allow_user   
    def ls_user(self,bot,update):
        all_user = db.get_all_username()
        strs=""
        i = 1
        for s in all_user:
            strs = strs + str(i)+" "+s+"\n"
            i = i + 1
        update.message.reply_text("Список всех пользователей: \n{}".format(strs))

    @is_admin_user
    @is_allow_user       
    def del_user(self,bot,update, **args):
        args_list=args["args"]
        if not (len(args_list)>0):
            update.message.reply_text("Формат команды: \\deluser имя_пользователя")
            return False
        db.del_user(args_list[0])
        self.ls_user(bot, update)
        return True
     # END обработчики командов администратора

        
    def reg_handler(self, command=None,hand=None,pass_args=False):
        """ регистрация команд которые обрабатывает бот """
        if (command is None) or (hand is None):
            return
        self.bot.dispatcher.add_handler(CommandHandler(command, hand,pass_args=pass_args))

    @is_allow_user        
    def about(self, bot, update):
        """ сообщает какие есть возможности у бота """
        update.message.reply_text("Если вы администратор бота, то вам доступны команды для управления пользователями.")
    

    @is_allow_user
    def start(self, bot, update):
        update.message.reply_text('Добро пожаловать, {}! Я бот который поможет вам вести свою библиотеку и позволит вам читать книги. '.format(update.message.from_user.first_name)) #, reply_markup=reply_markup)
        

    def docs(self, bot, update):
        bot.send_message(chat_id=update.message.chat_id, text = "Отправка файла...ждите...")
        bot.send_document(chat_id=update.message.chat_id, document=open('files/1.xlsx', 'rb'))
        

    def inlinebutton(self, bot, update):
        query = update.callback_query
        number_book = query.data
        #nameuser = update.message.from_user.username
        
        bot.edit_message_text(text="{}".format(query.data),
                            chat_id=query.message.chat_id,
                            message_id=query.message.message_id) 
        

    def error(bot, update, error):
        """Log Errors caused by Updates."""
        logger.warning('Update "%s" caused error "%s"', update, error)

    def run(self):
        """ запуск бота """   
        logging.debug("Start telegram bot")  
        self.bot.start_polling()
        self.bot.idle()


if __name__=="__main__":
    cfg = Config("config.ini")
    tgbot = iReadLibTelegramBot(cfg.token,logging.DEBUG)
    tgbot.run()