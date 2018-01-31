"""
    Класс данных БД
"""
import sqlite3
import os

class DbLib:
    def __init__(self,namefile):
        if not os.path.exists(namefile):
            self.conn = sqlite3.connect(namefile)
            self.c = self.conn.cursor()
            # Create table                        
            self.c.execute('''CREATE TABLE users
                        (id integer, nameuser text, role text)''')
            self.c.execute('''CREATE TABLE books
                        (id integer, namebook text, path text, currentpage integer, description text)''')
        else:
            self.conn = sqlite3.connect(namefile)
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

    # END методы для работы с таблицей User

    # методы для работы с таблицей Books
    def add_book(self):
        pass

    def del_book(self):
        pass
    
    def edit_book(self):
        pass
    # END методы для работы с таблицей Books

    def closedb(self):
        self.conn.close()

"""
# Insert a row of data
c.execute("INSERT INTO stocks VALUES ('2006-01-05','BUY','RHAT',100,35.14)")

# Save (commit) the changes


# We can also close the connection if we are done with it.
# Just be sure any changes have been committed or they will be lost.

"""