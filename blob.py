import mysql.connector

# 連接到 MySQL 資料庫
conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='Ff29098796',
    database='MBTI'
)
cursor = conn.cursor()

# 將圖片讀取為二進制數據
with open("C:\\Users\\ivan1\\OneDrive\\桌面\\下載.jpg", 'rb') as file:
    binary_data = file.read()

# 插入數據
insert_query = '''
INSERT INTO `使用者帳戶` (`UserID`, `UserName`, `Email`, `Password`, `ProfilePicture`, `LastActive`, `MBTI`, `機器人回話type`, `生日`, `年齡`, `星座`)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
'''

values = (
    1,
    '陳俊諺',
    '410630734@gms.tku.edu.tw',
    'Aa12345678',
    binary_data,
    '2024-01-12',
    'INFJ',
    '開心',
    '2002-11-19',
    21,
    '天蠍座'
)

cursor.execute(insert_query, values)
conn.commit()

cursor.close()
conn.close()

print("圖片已成功插入到資料庫")
