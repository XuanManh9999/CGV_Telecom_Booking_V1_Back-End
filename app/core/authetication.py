import cx_Oracle
from dotenv import load_dotenv
import os
import base64
from hashlib import sha1
import pandas as pd


load_dotenv()

def authenticate_user(username, password):
    # hash password
    hashed_password = sha1(password.encode()).digest()
    # convert to base64
    hashed_password = base64.b64encode(hashed_password).decode('utf-8')

    # get user from database
    try:
        # connect to oracle database
        conn = cx_Oracle.connect(user=os.getenv('ORACLE_USER'), password=os.getenv('ORACLE_PASSWORD'), dsn=os.getenv('ORACLE_DSN'))
        
        # create cursor to execute query
        cursor = conn.cursor()
        sqlC="""select decode(b.user_id,null,a.user_id,b.user_id) user_id,a.user_name,a.email,decode(b.is_role,null,case when a.user_id = 623 then 1 else decode(role_id,2,1,88,2,4) end,b.is_role) role,decode(a.chat_id,null,1291548626,a.chat_id) chat_id from users a left join (select * from sale_group where status=1) b on a.user_id=b.user_id where a.status=1 and a.user_name =upper('"""+username+"""') AND a.password='"""+str(hashed_password)+"""'"""
        
        cursor.execute(sqlC)
        account = cursor.fetchone()
        if account:
            id = account[0]
            username = account[1]
            role = account[3]
            chat_id = account[4]
            return id, username, role, chat_id
        else:
            return False
    except Exception as e:
        print(e)
        return False
    finally:
        if cursor:
            cursor.close()