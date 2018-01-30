from dblib import DbLib

db = DbLib("db/tst.db")

#db.add_user("Oilnur","administartor")
#db.add_user("andrey","user")

print(db.is_user("oilnur"))