import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
import requests

def search_tutorials(query, limit=5):
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
    sql = f"SELECT title, summary, url FROM tutorials WHERE {where_clause} LIMIT {limit}"

    cur.execute(sql, params)
    results = cur.fetchall()

    cur.close()
    conn.close()

    return results

def ask_gemini(question, tutorials):
    context = ""
    if tutorials:
        context = "Here are some relevant tutorials that were found:\n\n"
        for t in tutorials:
            context += f"- {t['title']}: {t['summary']} ({t['url']})\n"
    else:
        context = "No matching tutorials were found in the database.\n"

    prompt = f"""You are a helpful DIY troubleshooting assistant for a home improvement and auto mechanics app.

{context}

A user is asking: "{question}"

Using the tutorials above as reference where relevant, give a clear, practical, step-by-step answer. If the tutorials don't fully cover it, use your own knowledge to fill in the gaps. Keep the tone friendly and easy to follow for a beginner."""

    api_key = os.environ["GEMINI_API_KEY"]
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }

    response = requests.post(url, json=payload)
    response.raise_for_status()
    data = response.json()

    answer = data["candidates"][0]["content"]["parts"][0]["text"]
    return answer

if __name__ == "__main__":
    question = sys.argv[1]

    tutorials = search_tutorials(question)
    answer = ask_gemini(question, tutorials)

    print(answer)
