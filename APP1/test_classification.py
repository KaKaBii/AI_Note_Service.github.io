import uuid
import sqlite3
from extension.gpt_classification import GPT_classification

# 資料路徑設定
DATABASE = r"C:\Users\$H4I000-DSJPQSO1H1NP\OneDrive - 國立中央大學\文件\研究所\人工智慧設計與思考\AI_Note_Service.github.io\APP1\instance\database.db"

# 將逐字稿分類
def classify_contents(name, timestamp):
    command = "SELECT name, content FROM transcripts WHERE name = '{}' ORDER BY timestamp DESC LIMIT 1".format(name)
    print("Start GPT classification")
    name, result = GPT_classification(DATABASE_PATH=DATABASE, sql_command=command)
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        for category in result:
            if len(result[category]) != 0:
                for speaker in result[category]:
                    cursor.execute(
                        "INSERT INTO GPT_ClassificationResults VALUES ('{}', '{}', '{}', '{}')".format(
                            name, category, speaker, timestamp))
                    conn.commit()
        conn.close()
    except Exception as e: 
        raise e
    
if  __name__ == '__main__':
    name = "測試機器人"
    timestamps = [
        "2025-01-02 10:29:00",
        "2024-12-16 19:56:00",
        "2024-11-29 10:13:00",
        "2024-11-20 17:16:00",
        "2024-11-12 12:13:00"

    ] 
    for timestamp in timestamps:
        classify_contents(name, timestamp)
