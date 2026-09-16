import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor

def search_tutorials(query, limit=10):
conn = psycopg2.connect(os.environ["DATABASE_URL"])
cur = conn.cursor(cursor_factory=RealDictCursor)

words = query.lower().split()

conditions = []
params = []
for word in words:
    conditions.append("(LOWER(title) LIKE %s OR LOWER(description) LIKE %s)")
    params.append(f"%{word}%")
    params.append(f"%{word}%")

where_clause = " AND ".join(conditions) if conditions else "TRUE"

sql = f"""
    SELECT id, title, description, url
    FROM tutorials
    WHERE {where_clause}
    LIMIT %s
"""
params.append(limit)

cur.execute(sql, params)
results = cur.fetchall()

cur.close()
conn.close()
return results
if name == "main":
if len(sys.argv) < 2:
print('Usage: python search.py "your search phrase"')
sys.exit(1)

query = " ".join(sys.argv[1:])
results = search_tutorials(query)

if not results:
    print(f"No results found for: {query}")
else:
    print(f"Found {len(results)} result(s) for: {query}")
    for r in results:
        print(f"- {r['title']}")
        print(f"  {r['url']}")
 

