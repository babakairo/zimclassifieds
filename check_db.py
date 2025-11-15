import sqlite3

DB='zimclassifieds.db'
conn=sqlite3.connect(DB)
cur=conn.cursor()
cur.execute('SELECT COUNT(*) FROM users')
users=cur.fetchone()[0]
cur.execute('SELECT COUNT(*) FROM listings WHERE category="relationships"')
rels=cur.fetchone()[0]
print('users', users)
print('relationship_listings', rels)
conn.close()