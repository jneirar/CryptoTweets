import psycopg2

conn = psycopg2.connect(
    host="/tmp/",
    database="cryptotweets",
    user="postgres",
    password="postgres"
)

cur = conn.cursor()
cur.execute("SELECT * FROM users")
users = cur.fetchall()
print(users)
cur.close()

conn.close()
