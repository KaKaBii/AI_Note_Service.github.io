# 環境依賴
import os
import gc
import time
import uuid
import sqlite3
import asyncio
import logging
import requests
import subprocess
import ailabs_asr.transcriber as t
from datetime import datetime
from ailabs_asr.streaming import StreamingClient 
from flask import Flask, render_template, request, jsonify
from extension.gpt_classification import GPT_classification
from extension.closingReportOutput import ClosingReportOutput
from ailabs_asr.types import ModelConfig, TranscriptionConfig
from concurrent.futures import as_completed, ThreadPoolExecutor, TimeoutError

# AudioSegment.converter = r"C:\Users\h5073\AppData\Local\Programs\Python\ffmpeg\bin\ffmpeg.exe"

app = Flask(__name__)

# 設置錯誤日誌
logging.basicConfig(level=logging.ERROR)

# 資料路徑設定
DATABASE_FOLDER = os.path.join(app.root_path, 'instance')
UPLOAD_FOLDER = os.path.join(app.root_path, 'uploads')
DATABASE = os.path.join(DATABASE_FOLDER, 'database.db')

# 確保所有需要的文件夾存在
for folder in [DATABASE_FOLDER, UPLOAD_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# 設定允許的檔案類型
ALLOWED_EXTENSIONS = {'mp3', 'aac', 'flac', 'ogg', 'wav', 'm4a'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 定義根目錄
@app.route('/')
def index():
    return render_template('index.html')

# 定義分類目錄入口
@app.route('/classify')
def classify():
    return render_template('class.html')

# 定義總結頁面
@app.route('/summary')
def summaryPage():
    return render_template('summary.html')

#定義身體頁面
@app.route('/category/body')
def bodyPage():
   return render_template('classTemplate.html', title = "BODY")

#定義心靈頁面
@app.route('/category/psycho')
def psychoPage():
   return render_template('classTemplate.html', title = "PSYCHO")

#定義社會頁面
@app.route('/category/social')
def socialPage():
   return render_template('classTemplate.html', title = "SOCIAL")

#定義特殊頁面
@app.route('/category/special')
def specialPage():
   return render_template('classTemplate.html', title = "SPECIAL")

#定義其他頁面
@app.route('/category/extra')
def extraPage():
   return render_template('classTemplate.html', title = "EXTRA")

# 查詢月份列表
@app.route('/fetchMonthList', methods=['GET']) 
def fetchMonthList():
    person = request.args.get('person')  # 從請求中獲取人名參數

    if not person:
        return jsonify({'error': 'No person provided'}), 400

    try:
        # 使用 with 語句管理資料庫連線
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT strftime('%Y-%m', timestamp) FROM GPT_ClassificationResults WHERE name = ? ORDER BY timestamp", (person,))  # 假設表格名稱為 'GPT_ClassificationResults'，字段名稱為 'timestamp'
            months = [row[0] for row in cursor.fetchall()]

        return jsonify(months)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 查詢姓名列表
@app.route('/fetchNameList', methods=['GET']) 
def fetchNameList():
    try:
        # 使用 with 語句管理資料庫連線
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM nameList")  # 假設表格名稱為 'nameList'，字段名稱為 'name'
            names = [row[0] for row in cursor.fetchall()]
        return jsonify(names)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 新增姓名到資料庫
@app.route('/addName', methods=['POST'])
def addName():
    try:
        data = request.get_json()
        new_name = data.get('name')
        if not new_name:
            return jsonify({'error': 'No name provided'}), 400
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO nameList (name) VALUES (?)", (new_name,))
        conn.commit()
        conn.close()
        return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 查詢指定人名的逐字稿
@app.route('/fetchTranscripts', methods=['GET'])
def fetchTranscripts():
    person = request.args.get('person')  # 從請求中獲取人名參數

    if not person:
        return jsonify({'error': 'No person provided'}), 400

    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        # 根據名稱查詢逐字稿
        cursor.execute("SELECT content, timestamp FROM transcripts WHERE name = ? ORDER BY timestamp DESC", (person,))
        rows = cursor.fetchall()
        transcripts = [{'content': row[0], 'timestamp': row[1]} for row in rows]
        conn.close()
        app.logger.info(f'Transcripts fetched for {person}: {transcripts}')
       
        return jsonify(transcripts)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 新增指定人名的逐字稿
@app.route('/uploadSpecialTranscript', methods=['POST'])
def uploadSpecialTranscript():
    data = request.get_json()
    name = data.get('name')
    content = data.get('content')
    save_special_to_db(name, content)
    return jsonify({'message': 'Transcript uploaded successfully'}), 200

# 新增指定人名的特殊分類內容
@app.route('/uploadTranscript', methods=['POST'])
def uploadTranscript():
    data = request.get_json()
    name = data.get('name')
    content = data.get('content')
    save_transcript_to_db(name, content)
    return jsonify({'message': 'Transcript uploaded successfully'}), 200

# 編輯指定人名的逐字稿
@app.route('/editTranscript', methods=['POST'])
def editTranscript():
    data = request.get_json()
    timestamp = data.get('timestamp')
    new_content = data.get('newContent')

    if not timestamp or not new_content:
        app.logger.error('Timestamp or new content is missing in the request')
        return jsonify({'error': 'Timestamp or new content is missing'}), 400

    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("UPDATE transcripts SET content = ? WHERE timestamp = ?", (new_content, timestamp))
        conn.commit()
        conn.close()
        app.logger.info(f'Transcript edited at {timestamp}')
        return jsonify({'message': 'Transcript edited successfully'}), 200
    except Exception as e:
        app.logger.error(f'Error editing transcript at {timestamp}: {e}')
        return jsonify({'error': str(e)}), 500

# 刪除指定人名的逐字稿
@app.route('/deleteTranscript', methods=['POST'])
def deleteTranscript():
    data = request.get_json()
    timestamp = data.get('timestamp')

    if not timestamp:
        app.logger.error('Timestamp is missing in the request')
        return jsonify({'error': 'Timestamp is missing'}), 400

    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM transcripts WHERE timestamp = ?", (timestamp,))
        conn.commit()
        conn.close()
        app.logger.info(f'Transcript deleted at {timestamp}')
        return jsonify({'message': 'Transcript deleted successfully'}), 200
    except Exception as e:
        app.logger.error(f'Error deleting transcript at {timestamp}: {e}')
        return jsonify({'error': str(e)}), 500

# 確保音訊格式正確
def ensure_audio_format(input_file, output_file=None):
    """
    將音訊檔檢查並轉換為符合指定格式的 WAV 檔案：
    16kHz, 單聲道, 16位深度 (PCM 格式)。
    """
    
    try:
        print("開始處理音訊格式轉換")
        
        # 確認輸入檔是否存在
        if not os.path.isfile(input_file):
            raise FileNotFoundError(f"找不到檔案: {input_file}")
        print("輸入檔存在")
        
        # 檢查檔案副檔名是否支援
        file_extension = os.path.splitext(input_file)[1][1:].lower()
        print(f"檔案副檔名: {file_extension}")
        if file_extension not in ALLOWED_EXTENSIONS:
            raise ValueError(f"不支援的音訊格式: {file_extension}.")
        print("音訊格式受支持")
        
        # 自動生成輸出檔案名稱
        if output_file is None:
            output_file = os.path.splitext(input_file)[0] + '_processed.wav'
        print(f"輸出檔案路徑: {output_file}")

        # 設定 ffmpeg 的路徑
        ffmpeg_path = os.path.join(app.root_path, 'extension', 'ffmpeg', 'bin', 'ffmpeg.exe')

        # 確認 ffmpeg 可用
        if not os.path.isfile(ffmpeg_path):
            raise RuntimeError(f"ffmpeg 無法找到，檢查路徑是否正確：{ffmpeg_path}")
        print(f"ffmpeg 路徑: {ffmpeg_path}")

        # 構建轉換命令
        command = [
            ffmpeg_path,
            #"ffmpeg",
            '-i', input_file,
            '-ar', '16000',        # 采樣率 16kHz
            '-ac', '1',            # 單聲道
            '-sample_fmt', 's16',  # 16位深度
            output_file
        ]
        print(f"執行命令：{' '.join(command)}")
        
        # 執行轉換命令
        result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("ffmpeg 執行成功")
        print(result.stdout.decode())
        # print(f"音頻已成功轉換並保存：{output_file}")
        
        return output_file
    
    except subprocess.CalledProcessError as e:
        print(f"ffmpeg 執行失敗：{e}")
        print(e.stderr.decode())
        raise Exception(f"處理失敗: {e.stderr.decode()}")
    except Exception as e:
        print(f"音訊格式處理失敗：{e}")
        raise Exception(f"處理失敗: {e}")
    finally:
        # 顯式釋放資源
        gc.collect()

# 包裝函數來控制超時
async def process_with_timeout(func, audio_data, timeout):
    try:  
        await asyncio.wait_for(func(audio_data), timeout)  
    except asyncio.TimeoutError:  
        print(f"Function exceeded {timeout} seconds. Terminating...")  
        # await another_function()

# 雅婷語音轉文字模組(語者分離)
async def yating_api(file_path):
    """
    使用語音轉文字模塊來處理音頻文件，將音頻文件轉換為文本。
    """
    
    async def _convert(audio, result, api_key):
        try:
            model = ModelConfig('asr-zh-tw-std')
            config = TranscriptionConfig(True, True, 2, False)
            c = t.Transcriber(api_key, model, config)
            multiple_tasks = []
            for _ in range(2):
                transcript = c.transcribe(audio)
                task = transcript.wait_for_completion_async()
                multiple_tasks.append(task)

            for task in as_completed(multiple_tasks):
                result.append(task.result().transcript)
        except asyncio.CancelledError:
            print("Conversion was cancelled.") 
        return result
    
    # 獲取金鑰檔案
    current_dir = os.getcwd()
    key_file_path = os.path.join(current_dir, 'key.txt')
    
    if not os.path.exists(key_file_path):
        raise FileNotFoundError(f"檔案 '{key_file_path}' 不存在，請檢查檔案路徑或內容！")

    # 繼續讀取金鑰
    with open(key_file_path, 'r') as file:
        api_key = file.read().strip()
        if api_key == "" or None:
            raise FileNotFoundError(f"金鑰為空！")

    fileName = file_path
    headers = {'key': api_key}
    files = {'file': open(fileName, 'rb')}
    response = requests.post('https://asr.api.yating.tw/v1/uploads',
                             headers=headers,
                             files=files)
    print(response)
    audio = response.json()["url"]
    transcript = []
    # transcript = asyncio.run(_convert(audio, transcript, api_key))
    transcript = asyncio.get_event_loop().create_task(_convert(audio, transcript, api_key))
    return transcript

# 雅婷語音轉文字模組(即時)
def yating_runtime_api(file_path):
    # 獲取金鑰檔案
    current_dir = os.getcwd()
    key_file_path = os.path.join(current_dir, 'key.txt')
    
    if not os.path.exists(key_file_path):
        raise FileNotFoundError(f"檔案 '{key_file_path}' 不存在，請檢查檔案路徑或內容！")

    # 繼續讀取金鑰
    with open(key_file_path, 'r') as file:
        api_key = file.read().strip()
        if api_key == "" or None:
            raise FileNotFoundError(f"金鑰為空！")

    transcript = []
    def on_processing_sentence(message):
        print(f'hello: {message["asr_sentence"]}')

    def on_final_sentence(message):
        transcript.append(message["asr_sentence"])
        #print(f'world: {message["asr_sentence"]}')
        
    asr_client = StreamingClient(key=api_key)

    # 開始語音轉文字處理
    asr_client.start_streaming_wav(
        pipeline='asr-zh-tw-std',
        file=file_path,
        #on_processing_sentence=on_processing_sentence,
        on_final_sentence=on_final_sentence
    )
    return transcript

# 語音轉文字模塊
def transcribe_audio(file_path):
    transcript = asyncio.run(process_with_timeout(yating_api, file_path, timeout=60))  # 設定超時 60 秒
    transcribeMode = 0

    if transcript is None:
        # 如果第一個模塊超時，則使用第二個模塊
        transcript = yating_runtime_api(file_path)
        transcribeMode = 1

    # 如果兩個模塊都失敗，返回錯誤
    if transcript is None:
        transcribeMode = 2
        raise TimeoutError
    
    return transcript, transcribeMode

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
    except Exception as e: app.logger.error(f'Error: {e}')

# 獲得分類後的逐字稿
@app.route('/fetchClassifiedContent', methods=['GET'])
def fetchClassifiedContent():
    # 從請求參數中獲取 person 和 category_type
    person = request.args.get('person')  # 取得人名參數
    category_type = request.args.get('type')  # 取得類型參數

    content_data = []  # 初始化 content_data 變數為空列表
    try:
        if not person or not category_type:
            return jsonify({'error': 'Missing required parameters: person or type'}), 400

        # 連接資料庫
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        # 根據名字和類型查詢資料
        query = "SELECT content, timestamp FROM GPT_ClassificationResults WHERE name = ? AND type = ?"
        cursor.execute(query, (person, category_type))

        # 獲取查詢結果
        rows = cursor.fetchall()
        content_datas = [{'content': row[0], 'timestamp': row[1]} for row in rows]
        conn.close()
        unique_dates = sorted([date for date in {datetime.strptime(data["timestamp"], "%Y-%m-%d %H:%M:%S") for data in content_datas}])
        content_data = []
        for unique_date in unique_dates:
            content = ""
            for data in content_datas:
                if datetime.strptime(data["timestamp"], "%Y-%m-%d %H:%M:%S") == unique_date:
                    content += "{}\n".format(data["content"])
            content_data.append({'content': content, 'timestamp': unique_date.strftime("%Y-%m-%d %H:%M:%S")})

        # 日誌打印輸出的資料
        app.logger.info(f"Classified content fetched for {person} and category {category_type}: {content_data}")

        return jsonify(content_data)

    except Exception as e:
        app.logger.error(f"Error fetching classified content for {person} and category {category_type}: {e}")
        return jsonify({'error': str(e)}), 500

# 獲得總結報告
@app.route('/fetchSummaryContent', methods=['GET'])
def fetchSummaryContent():
    # 從請求參數中獲取 person
    person = request.args.get('person')  # 取得人名參數
    # fetchContent(person)

    content_data = []  # 初始化 content_data 變數為空列表
    try:
        if not person:
            return jsonify({'error': 'Missing required parameters: person or type'}), 400

        # 連接資料庫
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        # 根據名字和類型查詢資料
        query = "SELECT content, time FROM ClosingReport WHERE name = ?"
        cursor.execute(query, (person,))

        # 獲取查詢結果
        rows = cursor.fetchall()
        content_data = [{'content': row[0], 'timestamp': row[1]} for row in rows]
        conn.close()

        # 日誌打印輸出的資料
        app.logger.info(f"Summary content fetched for {person}: {content_data}")

        return jsonify(content_data)

    except Exception as e:
        app.logger.error(f"Error fetching summary content for {person}: {e}")
        return jsonify({'error': str(e)}), 500


# 獲得總結報告
@app.route('/generateSummaryContent', methods=['GET'])
def generateSummaryContent():
    # 從請求參數中獲取 person
    person = request.args.get('person')  # 取得人名參數
    month = request.args.get('month')  # 取得月份參數
    try:
        if not person:
            return jsonify({'error': 'Missing required parameters: person or type'}), 400
        
        fetchContent(person, month)

        content_data = []  # 初始化 content_data 變數為空列表
        # 連接資料庫
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        # 根據名字和類型查詢資料
        query = "SELECT content, time FROM ClosingReport WHERE name = ?"
        cursor.execute(query, (person,))

        # 獲取查詢結果
        rows = cursor.fetchall()
        content_data = [{'content': row[0], 'timestamp': row[1]} for row in rows]
        conn.close()

        # 日誌打印輸出的資料
        app.logger.info(f"Summary content fetched for {person}: {content_data}")

        return jsonify(content_data)

    except Exception as e:
        app.logger.error(f"Error fetching summary content for {person}: {e}")
        return jsonify({'error': str(e)}), 500

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
                isContent = False
                for transcript in transcripts:
                    if transcript["type"] == type and datetime.strptime(transcript["timestamp"], "%Y-%m-%d %H:%M:%S").date() == date and datetime.strptime(transcript["timestamp"], "%Y-%m-%d %H:%M:%S").date().month == timestamp.month:
                        if transcript["content"] != None:
                            chatContent += "{}\n".format(transcript["content"])
                            isContent = True
                if isContent == False:
                    chatContent += "空白\n"
        print(chatContent)
        cursor.execute("INSERT INTO ClosingReport VALUES ('{}', '{}-{}', '{}')".format(name, timestamp.year, timestamp.month, ClosingReportOutput(chatContent)))
        conn.commit()
        conn.close()
    except Exception as e:
        print(e)
        app.logger.error(f"Error occurred while fetching content: {e}")
        return "Internal Server Error", 500
    
def fetchContent(name, month):
    try:
        print(f"生成{name}的{month}月總結報告")
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        timestamp = datetime.strptime(month, '%Y-%m')
        query = "SELECT name, type, content, timestamp FROM GPT_ClassificationResults WHERE name = ? AND strftime('%Y-%m', timestamp) = ? ORDER BY timestamp"
        cursor.execute(query, (name, month))
        #cursor.execute(query, ("{name}", "{month}"))
        rows = cursor.fetchall()
        transcripts = [{'user': row[0], 'type': row[1], 'content': row[2], 'timestamp': row[3]} for row in rows]
        #print(transcripts)
        if not transcripts:
            print("No transcripts found")

        unique_dates = sorted([date for date in {datetime.strptime(transcript["timestamp"], "%Y-%m-%d %H:%M:%S").date() for transcript in transcripts}])
        unique_types = {transcript["type"] for transcript in transcripts}
        #print("Unique dates:", unique_dates)
        #print("Unique types:", unique_types)

        chatContent = "{}\n".format(name)
        for type in unique_types:
            chatContent += "{}\n".format(type)
            for date in unique_dates:
                chatContent += "{}\n".format(date)
                isContent = False
                for transcript in transcripts:
                    if transcript["type"] == type and \
                    datetime.strptime(transcript["timestamp"], "%Y-%m-%d %H:%M:%S").date() == date:
                        if transcript["content"] != None:
                            #print("Content found:", transcript["content"])
                            chatContent += "{}\n".format(transcript["content"])
                            isContent = True
                if isContent == False:
                    chatContent += "空白\n"
        print(chatContent)
        cursor.execute("INSERT INTO ClosingReport VALUES ('{}', '{}-{}', '{}')".format(name, timestamp.year, timestamp.month, ClosingReportOutput(chatContent)))
        conn.commit()
        conn.close()
    except Exception as e:
        print(e)
        app.logger.error(f"Error occurred while fetching content: {e}")
        return "Internal Server Error", 500
    
# @app.route('/category/<category_type>', methods=['GET'])
# def classify_Togo(category_type):
#     # 假設我們根據 URL 參數中的分類類型來獲取分類內容
#     # 可以根據需求更改這裡獲取 'name' 的方式
#     """ original code
#     # name = request.args.get('name')  # 假設 'name' 也來自 URL 或查詢參數

#     # if not name:
#     #     return jsonify({'error': 'No name provided'}), 400
#     """

#     ### test code
#     name = "測試機器人"
#     ###

#     try:
#         # 調用 fetchClassifiedContent 函數來獲取分類內容
#         content_data = fetchContent(name)

#         # 如果有資料，渲染頁面並將分類內容傳遞給前端
#         if content_data:
#             return render_template('classTemplate.html', title=category_type.upper(), content_data=content_data)
#         else:
#             # 如果查無資料，顯示空的分類頁面
#             return render_template('classTemplate.html', title=category_type.upper(), content_data=[])

#     except Exception as e:
#         app.logger.error(f"Error occurred while fetching content for category {category_type}: {e}")
#         return "Internal Server Error", 500

# 將逐字稿保存到資料庫
def save_transcript_to_db(user, content):
    """
    將逐字稿保存到資料庫中。
    """
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if not user or not content:
            app.logger.error('Name or content is missing in the request')
            return jsonify({'error': 'Name or content is missing'}), 400
        
        cursor.execute("INSERT INTO transcripts (name, content, timestamp) VALUES (?, ?, ?)", (user, content, timestamp))
        
        conn.commit()
        conn.close()
        print(f"逐字稿已成功儲存到資料庫，使用者：{user}")
        app.logger.info(f'Transcript uploaded for {user} at {timestamp}')
        classify_contents(name=user, timestamp=timestamp)
    except Exception as e:
        app.logger.error(f'Error uploading transcript for {user}: {e}')
        return jsonify({'error': str(e)}), 500

# 將逐字稿保存到資料庫
def save_special_to_db(user, content):
    """
    將特殊內容保存到資料庫中。
    """
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if not user or not content:
            app.logger.error('Name or content is missing in the request')
            return jsonify({'error': 'Name or content is missing'}), 400
        
        cursor.execute("INSERT INTO GPT_ClassificationResults (name, type, content, timestamp) VALUES (?, ?, ?, ?)", (user, "特殊", content, timestamp))
        
        conn.commit()
        conn.close()
        print(f"特殊內容已成功儲存到資料庫，使用者：{user}")
        app.logger.info(f'Transcript uploaded for {user} at {timestamp}')
    except Exception as e:
        app.logger.error(f'Error uploading transcript for {user}: {e}')
        return jsonify({'error': str(e)}), 500
    
# 上傳錄音檔
@app.route('/uploadRecord', methods=['POST'])
def upload_record():
    print("接收到上傳請求")
    converted_file_path = None  # 初始化變數

    if 'file' not in request.files:
        print("沒有檔案被上傳")
        return jsonify({'success': False, 'message': '沒有檔案被上傳'}), 400
    
    file = request.files['file']
    print(f"接收到的文件名稱：{file.filename}")

    if file.filename == '':
        print("文件名稱為空")
        return jsonify({'error': 'No selected file'}), 400

    # 檢查文件是否符合允許的類型
    if not allowed_file(file.filename):
        print(f"不允許的文件類型：{file.filename}")
        return jsonify({'error': 'File type not allowed'}), 400

    # 生成唯一文件名
    temp_file_path = os.path.join(UPLOAD_FOLDER, f"temp_{uuid.uuid4().hex}_{file.filename}")

    try:
        # 先儲存上傳的原始檔案到磁碟
        with open(temp_file_path, 'wb') as f:
            file.save(f)
        print(f"臨時文件已成功保存至：{temp_file_path}")

        # 轉換音頻格式並重新儲存
        converted_file_path = ensure_audio_format(temp_file_path)
        print(f"轉換文件已成功保存至：{converted_file_path}")

        print("正在轉換逐字稿......")
        contentList = []
        contents, transcribeMode = transcribe_audio(converted_file_path)
        print("轉換完成")
        if transcribeMode == 0:
            for i in range(len(contents[0])):
                if contents[0][i]['speakerId'] == "0":
                    contentList.append("{}：{}".format("講者１", contents[0][i]['sentence']))
                    print("{}：{}".format("講者１", contents[0][i]['sentence']))
                else:
                    contentList.append("{}：{}".format("講者２", contents[0][i]['sentence']))
                    print("{}：{}".format("講者２", contents[0][i]['sentence']))
        elif transcribeMode == 1:
            for i in range(len(contents)):
                if i%2==1:
                    contentList.append("{}：{}".format("講者１", contents[i]))
                    print("{}：{}".format("講者１", contents[i]))
                else:
                     contentList.append("{}：{}".format("講者２", contents[i]))
                     print("{}：{}".format("講者２", contents[i]))
  
        user = request.form.get('user')
        
        # 使用 join 生成合併後的內容
        transcript = "\n".join(contentList)
        
        print(transcript)    
        save_transcript_to_db(user, transcript)

    except Exception as e:
        print(f"音頻轉換失敗：{e}")
        return jsonify({'error': 'Audio conversion failed'}), 500
    
    finally:
        # 刪除原始文件
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        print(f"原始臨時文件已刪除：{temp_file_path}")

        # 刪除轉換文件（如果存在）
        if converted_file_path and os.path.exists(converted_file_path):
            print(f"轉換文件已刪除：{converted_file_path}")
            os.remove(converted_file_path)

    return jsonify({'message': 'File uploaded and converted successfully', 'converted_file_path': converted_file_path}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)