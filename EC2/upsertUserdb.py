import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
database = os.getenv('database')
user = os.getenv('user')
host = os.getenv('host')
password = os.getenv('password_db')
conn = psycopg2.connect(database = database,
                        user = user,
                        host = host,
                        password = password,
                        port = 5432)

cur = conn.cursor()
cur.execute(
    """
    insert into public.user ("id","full_name","email","status","last_login","access_rights","banned","ip",
							"application","created_at","subscription_status","subscription_type","last_login_datetime",
							"created_at_datetime","toexport","dataloader")
select "id","full_name","email","status","last_login","access_rights","banned","ip",
							"application","created_at","subscription_status","subscription_type","last_login_datetime",
							"created_at_datetime","toexport","dataloader" from public.temp_user
on conflict(id) do update set id=excluded.id, full_name=excluded.full_name, email=excluded.email,
							status=excluded.status, last_login=excluded.last_login, access_rights=excluded.access_rights,
							banned=excluded.banned, ip=excluded.ip, application=excluded.application,
							created_at=excluded.created_at, subscription_status=excluded.subscription_status,
							subscription_type=excluded.subscription_type, last_login_datetime=excluded.last_login_datetime,
							created_at_datetime=excluded.created_at_datetime, toexport=excluded.toexport, dataloader=excluded.dataloader;
    """
)

conn.commit()
conn.close()