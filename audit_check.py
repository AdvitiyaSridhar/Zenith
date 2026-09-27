import sqlite3
conn = sqlite3.connect(r'C:\Advi\Collegestuff\Events\SIH\zenith\backend\risk_assessment.db')
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
print('Tables:', c.fetchall())
conn.close()