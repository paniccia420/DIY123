import os
import psycopg2
from psycopg2.extras import RealDictCursor
import sys

def search_tutorials(query):
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    cur = conn.cursor(cursor_factory=RealDictCursor)

    words = query.split()
    conditions = []
    params = []
    for word in words:
        conditions.append("(title ILIKE %s OR summary ILIKE %s)")
        params.append(f"%{word}%")
        params.append(f"%{word}%")

    where_clause = " AND ".join(conditions)
    sql = f"SELECT id, title, summary, url FROM tutorials WHERE {where_clause} LIMIT 10"

    cur.execute(sql, params)
    results = cur.fetchall()

    cur.close()
    conn.close()

    return results

if __name__ == "__main__":
    query = sys.argv[1]
    results = search_tutorials(query)

    if not results:
        print("No results found.")
    else:
        for r in results:
            print(r["title"])
            print(r["url"])
            print("---")
