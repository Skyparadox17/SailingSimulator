import sqlite3

db = sqlite3.connect('data.db')

#Get a cursor object
cursor = db.cursor()
cursor.execute('''CREATE TABLE users(name TEXT, score NUMBER)''')
db.commit()


ans = True
while ans:
    print ("****MENU****")
    print("1. Enter new user score")
    print("2. View top 5 scores")
    print("3. View whole database")
    print("4. Clear down scores not in top 5")
    print("5. Quit database")

    selection = int(input("Select one number:  "))
    # Get a cursor object
    cursor = db.cursor()

    if selection == 1:
        cursor = db.cursor()
        name1 = str(input("name: "))
        score1 = str(input("score: "))

        # Insert user 1
        cursor.execute('''INSERT INTO users(name,score)
                          VALUES(?,?,?)''', (name1, score1))
        print('User information inserted')

        db.commit()

        res = cursor.execute('''SELECT * FROM users''')
        print(res.fetchall())

    elif selection == 2:
        # view top 5
        res = cursor.execute('''SELECT * FROM users order by score desc limit 5 ''')
        print(res.fetchall())

    elif selection == 3:
        # view all
        res = cursor.execute('''SELECT * FROM users''')
        print(res.fetchall())

    elif selection == 4:  # clear down scores not in top 5
        res = cursor.execute('''SELECT * FROM users order by score desc limit 5''')
        results = res.fetchall()
        lowestScore = results[len(results) - 1][2]
        print (lowestScore)
        res = cursor.execute('''DELETE FROM users WHERE score < ?''', (lowestScore,))

    elif selection == 5:  # quitting database, break outta loop
        print ("Quiting datatbase")
        db.close()
        break
    else:
        print ("Not a valid option")

# Get a cursor object
 #cursor = db.cursor()
 #cursor.execute('''DROP TABLE users''')
 #db.commit()
