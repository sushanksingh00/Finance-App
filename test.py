<<<<<<< HEAD
import sqlite3
from helpers import lookup

db = sqlite3.connect('finance.db', check_same_thread=False)

c = db.cursor()

name = 'sush'
c.execute('SELECT * FROM users WHERE username= ?', (name,) ) # here it says an error that index value of range when i call up for the row[0][3] in next line how do i get the session users list 
rows = c.fetchall()

total_money_of_user = rows[0][3]

print(total_money_of_user)

=======
import sqlite3
from helpers import lookup

db = sqlite3.connect('finance.db', check_same_thread=False)

c = db.cursor()

name = 'sush'
c.execute('SELECT * FROM users WHERE username= ?', (name,) ) # here it says an error that index value of range when i call up for the row[0][3] in next line how do i get the session users list 
rows = c.fetchall()

total_money_of_user = rows[0][3]

print(total_money_of_user)

>>>>>>> 6331065 (hello)
