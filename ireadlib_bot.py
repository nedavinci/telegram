from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, Filters, RegexHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
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
    return

def get_file(namefile):
    """
        получение содержимого файла, если файла нет, то возвращается None
    """
    result = None
    if not os.path.exists(namefile):
        return result
    with open(namefile,"r") as f:
        result = f.read()
    return result


    
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


NAMEBOOK, AUTHORBOOK, BOOK, READ = range(4)

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
       
        conv_handler_readbook = ConversationHandler(
            entry_points=[CommandHandler('read', self.choose_book)],
            states={
                READ: [MessageHandler(Filters.text, self.read_book)]
            },
            fallbacks=[CommandHandler('cancelread', self.cancel_read)]
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
        self.bot.dispatcher.add_handler(conv_handler_readbook)
        # регистрация команд     
        self.reg_handler("start",self.start)
        self.reg_handler("help",self.about)
        # команды администратора
        self.reg_handler("adduser",self.add_user, True)
        self.reg_handler("lsuser",self.ls_user)
        self.reg_handler("deluser",self.del_user, True)
        #self.reg_handler("read",self.choose_book)
        # END команды администратора
        self.reg_handler("lsbook",self.ls_book)
        # END регистрация команд

    # обработчики диалога readbook - чтение книги
    @is_allow_user
    def choose_book(self, bot, update):
        """
            чтение книги
        """
        id_books = self.ls_book(bot, update)
        if len(id_books) == 0:
            update.message.reply_text("Чтение невозможно.")
            return ConversationHandler.END
        
        update.message.reply_text('Выберите книгу..') #, reply_markup=reply_markup)
        return READ

    def read_book(self,bot,update, **args):
        #print("ФУНКЦИЯ read_book ")
        nameuser = update.message.from_user.username
        #query = update.callback_query
        read_keyboard = [['Назад', 'Вперёд'], ['Завершить чтение']]
        readbook_markup = ReplyKeyboardMarkup(read_keyboard, one_time_keyboard=True)
        txt_message = update.message.text
        #print("ВВедённые данные:", txt_message)
        if txt_message == "Назад":
            current_page = db.get_currentpage_in_active_book(nameuser)
            current_page = current_page - 1
            if current_page <= 0:
                current_page = 1
            # здесь нужно вставить проверку на корректность страницы, не превышает ли она максимальную
            db.set_currentpage_in_active_book(nameuser, current_page)
            book = self.get_book_currentpage(nameuser, current_page)
            update.message.reply_text("Текущая страница: {0}\n{1}".format(current_page, book), reply_markup=readbook_markup)
            return READ

        if txt_message == "Вперёд":
            current_page = db.get_currentpage_in_active_book(nameuser)
            current_page = current_page + 1
            book = self.get_book_currentpage(nameuser, current_page)
            if book is not None:
                db.set_currentpage_in_active_book(nameuser, current_page)
            else:
                current_page = current_page - 1
                book = self.get_book_currentpage(nameuser, current_page)
                db.set_currentpage_in_active_book(nameuser, current_page)
            update.message.reply_text("Текущая страница: {0}\n{1}".format(current_page, book), reply_markup=readbook_markup)    
            return READ

        if txt_message == "Завершить чтение":
            db.set_noactive_book(nameuser)        
            reply_markup = ReplyKeyboardRemove()
            update.message.reply_text('Вы прервали чтение книги.', reply_markup=reply_markup)
            return ConversationHandler.END   

        if txt_message.isdigit():
            books = db.get_all_book(nameuser)
            for b in books:
                if b[0]==int(txt_message):
                    db.set_active_book(int(txt_message))
                    current_page = db.get_currentpage_in_active_book(nameuser)
                    if current_page <= 0:
                        current_page = 1
                    book = self.get_book_currentpage(nameuser, current_page)
                    if book is not None:
                        db.set_currentpage_in_active_book(nameuser, current_page)
                    else:
                        current_page = current_page - 1
                        book = self.get_book_currentpage(nameuser, current_page)
                        db.set_currentpage_in_active_book(nameuser, current_page)
                    update.message.reply_text("Текущая страница: {0}\n{1}".format(current_page, book), reply_markup=readbook_markup)    
                    return READ 
            reply_markup = ReplyKeyboardRemove()
            update.message.reply_text('Книги нет.', reply_markup=reply_markup)
            return ConversationHandler.END
        return READ       

    def cancel_read(self, bot, update):
        nameuser = update.message.from_user.username
        db.set_noactive_book(nameuser)        
        reply_markup = ReplyKeyboardRemove()
        update.message.reply_text('Вы прервали чтение книги.', reply_markup=reply_markup)
        return ConversationHandler.END
    


    # обработчики диалога readbook - чтение книги

    # обработчики диалога addbook
    @is_allow_user
    def add_book(self,bot,update, **args):
        bot.send_message(chat_id=update.message.chat_id, text = "Введите название книги.\n/cancel - отмена операции.")
        return NAMEBOOK
    
    def add_namebook(self,bot,update):
        nameuser = update.message.from_user.username
        namebook = update.message.text  
        book ={"author":"","book": "", "pathbook":"","currentpage":1,"description":""}
        book["book"] = namebook
        self.newbook[nameuser] =  book        
        bot.send_message(chat_id=update.message.chat_id, text = "Введите автора книги.\n/cancel - отмена операции.")
        return AUTHORBOOK
    
    def add_author(self,bot,update):
        nameuser = update.message.from_user.username
        authorbook = update.message.text  
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
        reply_markup = ReplyKeyboardRemove()
        update.message.reply_text('Добро пожаловать, {}! Я бот который поможет вам вести свою библиотеку и позволит вам читать книги. '.format(update.message.from_user.first_name), reply_markup=reply_markup)
        

    def docs(self, bot, update):
        bot.send_message(chat_id=update.message.chat_id, text = "Отправка файла...ждите...")
        bot.send_document(chat_id=update.message.chat_id, document=open('files/1.xlsx', 'rb'))
        

    def inlinebutton(self, bot, update):
        query = update.callback_query
        number_book = query.data
        
        bot.edit_message_text(text="{}".format(query.data),
                            chat_id=query.message.chat_id,
                            message_id=query.message.message_id) 
        # передать информацию о том какую книгу читаю
        return READ
        
    def get_book_currentpage(self, nameuser, current_page):
        #nameuser = update.message.from_user.username 
        path_book = db.get_path_active_book(nameuser)
        path_book_full = path_book +"/{0}.txt".format(current_page)
        result = get_file(path_book_full)
        return result

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