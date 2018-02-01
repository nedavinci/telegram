"""
    Класс данных БД
"""
import sqlite3
import os



class DbLib:
    def __init__(self,namefile):
        if not os.path.exists(namefile):
            self.conn = sqlite3.connect(namefile, check_same_thread=False)
            self.c = self.conn.cursor()
            # Create table                        
            self.c.execute('''CREATE TABLE users
                        (id integer, nameuser text, role text)''')
            self.c.execute('''CREATE TABLE books
                        (id integer, author text, namebook text, pathbook text, currentpage integer, description text)''')
        else:
            self.conn = sqlite3.connect(namefile, check_same_thread=False)
            self.c = self.conn.cursor()
    
    # методы для работы с таблицей User
    def add_user(self,nameuser,role):
        """
            добавляем пользователя, проверяем есть ли данный пользователь в таблице Users
        """
        if self.is_user(nameuser):
            return False
        self.c.execute("SELECT MAX(id) FROM users")
        # Получаем результат сделанного запроса
        id = self.c.fetchall()
        #print(id[0][0])
        if id[0][0] is None:
            id = 1
        else:
            id = int(id[0][0]) +1
        #print(id)
        str = "INSERT INTO users (id, nameuser, role) VALUES ({0},'{1}','{2}')".format(id,nameuser,role)
        #print(str)
        self.c.execute(str)
        self.conn.commit()
        return True

    def del_user(self,nameuser): 
        """
            удаление информации по пользователю из таблицы users
        """
        command = "DELETE FROM users WHERE nameuser = '{0}'".format(nameuser)       
        self.c.execute(command)
        self.conn.commit()
        return True
    
    def edit_user_role(self,nameuser,role):
        """
            редактирование роли у пользователя nameuser
        """
        command = "UPDATE users SET role='{0}' WHERE nameuser='{1}'".format(role,nameuser)
        self.c.execute(command)
        self.conn.commit()
        return True
    
    def is_user(self,nameuser):
        """
            возвращает True - если пользователь существует
        """
        self.c.execute("SELECT nameuser  FROM users WHERE nameuser='{}'".format(nameuser))
        user = self.c.fetchall()
        #print(user)
        if user == []:
            return False
        else:
            return True

    def get_id_user(self,nameuser):
        """
            получение id пользователя по имени, если пользователя нет, то возвращается None
        """
        if not self.is_user(nameuser):
            return None
        self.c.execute("SELECT id FROM users WHERE nameuser='{0}'".format(nameuser))
        # Получаем результат сделанного запроса
        id = self.c.fetchall()
        print(id[0][0])
        if id[0][0] is None:
            return None
        else:
            id = int(id[0][0])
        return id

    def get_all_username(self):
        """
            возвращает всех пользователей из таблицы Users
        """
        result=[]
        self.c.execute("SELECT nameuser  FROM users")
        users = self.c.fetchall()
        #print(users)
        for user in users:
            if user[0] is not None:
                result.append(user[0])
        return result
        

    # END методы для работы с таблицей User

    # методы для работы с таблицей Books
    def add_book(self,nameuser,book):
        """
            добавляем книгу пользователю nameuser. 
            book - это словарь с ключами namebook(название книги) , pathbook(путь до книги на диске) ,currentpage (текущая страница),  author - автор книги
        """
        id = self.get_id_user(nameuser)
        if id is None:
            return False
        
        str = "INSERT INTO books (id, author, namebook, pathbook, currentpage, description) VALUES ({0},'{1}','{2}','{3}',{4},'{5}')".format(id,book["author"],book["book"],book["pathbook"],book["currentpage"],book["description"])
        #git add print(str)
        self.c.execute(str)
        self.conn.commit()
        
        return True

    def is_namebook(self,namebook):
        """
            возвращает True - если название книги существует
        """
        self.c.execute("SELECT namebook  FROM books WHERE namebook='{}'".format(namebook))
        user = self.c.fetchall()
        if user == []:
            return False
        else:
            return True

    def del_book(self,namebook,author):
        pass
    
    def edit_book(self,book):
        """
            book - это словарь с ключами namebook(название книги) , pathbook(путь до книги на диске) ,currentpage (текущая страница),  author - автор книги
        """
        pass
    # END методы для работы с таблицей Books

    def closedb(self):
        self.conn.close()

