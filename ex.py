allow_users = [{"username":"Oilnur","id":"3608708"}]

# проверка на разрешенного пользователя
def i_sallow_user(nameuser):
    for user in allow_users:
        if user["username"]==nameuser:
            return True
    return False

print(i_sallow_user("Oilnur"))

print(i_sallow_user("oilnur"))