from dblib import DbLib

db = DbLib("db/tst.db")


db.add_user("Oilnur","administartor")
db.add_user("andrey","user")
db.add_user("andrey","user")
db.add_user("Oilnur","administartor")
db.edit_user_role("andreys","administartor")
#db.del_user("Oilnur")


book ={"author":"Петр Пен","book": "Твин Пикс", "pathbook":"/home/lib/a.txt","currentpage":56,"description":"обычное описание"}

db.add_book('andrey',book)
print(db.is_namebook(book["book"]))

# print(db.is_user("oilnur"))