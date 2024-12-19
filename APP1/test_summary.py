import uuid
from datetime import datetime
import sqlite3
from extension.closingReportOutput import ClosingReportOutput

# 資料路徑設定
DATABASE = r"C:\Users\$H4I000-DSJPQSO1H1NP\OneDrive - 國立中央大學\文件\研究所\人工智慧設計與思考\AI_Note_Service.github.io\APP1\instance\database.db"

def fetchContent(name):
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        timestamp = datetime.now()

        query = "SELECT name, type, content, timestamp FROM GPT_ClassificationResults WHERE name = ? AND timestamp LIKE ? ORDER BY timestamp"
        formatted_timestamp = f"{timestamp.year}-{timestamp.month}%"
        cursor.execute(query, (name, formatted_timestamp))
        rows = cursor.fetchall()
        transcripts = [{'user': row[0], 'type': row[1], 'content': row[2], 'timestamp': row[3]} for row in rows]
        unique_dates = sorted([date for date in {datetime.strptime(transcript["timestamp"], "%Y-%m-%d %H:%M:%S").date() for transcript in transcripts}])
        unique_types = {transcript["type"] for transcript in transcripts}
        chatContent = "{}\n".format(name)
        for type in unique_types:
            chatContent += "{}\n".format(type)
            for date in unique_dates:
                chatContent += "{}\n".format(date)
                for transcript in transcripts:
                    if transcript["type"] == type and datetime.strptime(transcript["timestamp"], "%Y-%m-%d %H:%M:%S").date() == date:
                        chatContent += "{}\n".format(transcript["content"])
        cursor.execute("INSERT INTO ClosingReport VALUES ('{}', '{}-{}', '{}')".format(name, timestamp.year, timestamp.month, ClosingReportOutput(chatContent)))
        conn.commit()
        conn.close()
    except Exception as e:
        raise e
    
if  __name__ == '__main__':
    name = "測試機器人"
    fetchContent(name)
