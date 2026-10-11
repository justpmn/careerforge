import psycopg


conn = psycopg.connect(
    "dbname=careerforge "
    "user=careerforge "
    "password=careerforge "
    "host=localhost "
    "port=5432"
)

cur = conn.cursor()


print("\nRESUMES")
cur.execute(
    """
    SELECT
        id,
        user_id,
        file_name,
        file_type
    FROM resumes
    ORDER BY id;
    """
)

for row in cur.fetchall():
    print(row)


print("\nUSER SKILLS")
cur.execute(
    """
    SELECT
        us.user_id,
        s.name,
        us.source
    FROM user_skills us
    JOIN skills s
        ON s.id = us.skill_id
    ORDER BY s.name;
    """
)

for row in cur.fetchall():
    print(row)


print("\nRECOMMENDATIONS")
cur.execute(
    """
    SELECT
        r.user_id,
        c.career_key,
        c.name,
        r.match_score
    FROM recommendations r
    JOIN careers c
        ON c.id = r.career_id
    ORDER BY
        r.created_at DESC,
        r.match_score DESC;
    """
)

for row in cur.fetchall():
    print(row)


cur.close()
conn.close()