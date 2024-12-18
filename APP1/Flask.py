# 環境依賴
import os
import gc
import sqlite3
import uuid
import subprocess
import asyncio
import requests
import logging
import ailabs_asr.transcriber as t
from datetime import datetime
# from ailabs_asr.streaming import StreamingClient 
from flask import Flask, render_template, request, jsonify
from extension.gpt_classification import GPT_classification
from ailabs_asr.types import ModelConfig, TranscriptionConfig
from concurrent.futures import as_completed

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
            # ffmpeg_path,
            "ffmpeg",
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

async def _convert(audio, result, api_key):
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
    return result

# 語音轉文字模塊
def transcribe_audio(file_path):
    """
    使用語音轉文字模塊來處理音頻文件，將音頻文件轉換為文本。
    """

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

    # transcript = []
    # def on_processing_sentence(message):
    #     print(f'hello: {message["asr_sentence"]}')

    # def on_final_sentence(message):
    #     transcript.append(message["asr_sentence"])
    #     #print(f'world: {message["asr_sentence"]}')
        
    # asr_client = StreamingClient(key=api_key)

    # # 開始語音轉文字處理
    # asr_client.start_streaming_wav(
    #     pipeline='asr-zh-tw-std',
    #     file=file_path,
    #     #on_processing_sentence=on_processing_sentence,
    #     on_final_sentence=on_final_sentence
    # )
    fileName = file_path
    headers = {'key': api_key}
    files = {'file': open(fileName, 'rb')}
    response = requests.post('https://asr.api.yating.tw/v1/uploads',
                             headers=headers,
                             files=files)
    audio = response.json()["url"]
    transcript = []
    transcript = asyncio.run(_convert(audio, transcript, api_key))
    
    return transcript

# 
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

# 
@app.route('/fetchClassifiedContent', methods=['GET'])
def fetchClassifiedContent():
    # 從請求中獲取分類類型參數和名字參數
    category_type = request.args.get('category')
    # 從 session 中獲取 person（之前在 fetchTranscripts 中儲存）
    person = session.get('person')  # 從 session 中獲取儲存的名字
    if not category_type or not person:
        return jsonify({'error': 'No category or name provided'}), 400

    content_data = []  # 初始化 content_data 變數為空列表
    try:
        # 連接資料庫
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        # 根據名字和類型查詢資料
        query = "SELECT content, timestamp FROM GPT_ClassificationResults WHERE name = ? AND type = ?"
        cursor.execute(query, (person, category_type))

        # 獲取查詢結果
        rows = cursor.fetchall()
        content_data = [{'content': row[0], 'timestamp': row[1]} for row in rows]
        conn.close()

        # 日誌打印輸出的資料
        app.logger.info(f"Classified content fetched for {person} and category {category_type}: {content_data}")

        return jsonify(content_data)

    except Exception as e:
        app.logger.error(f"Error fetching classified content for {person} and category {category_type}: {e}")
        return jsonify({'error': str(e)}), 500

# 
@app.route('/category/<category_type>', methods=['GET'])
def classify_Togo(category_type):
    # 假設我們根據 URL 參數中的分類類型來獲取分類內容
    # 可以根據需求更改這裡獲取 'name' 的方式
    name = request.args.get('name')  # 假設 'name' 也來自 URL 或查詢參數

    if not name:
        return jsonify({'error': 'No name provided'}), 400

    try:
        # 調用 fetchClassifiedContent 函數來獲取分類內容
        content_data = fetchClassifiedContent()

        # 如果有資料，渲染頁面並將分類內容傳遞給前端
        if content_data:
            return render_template('classTemplate.html', title=category_type.upper(), content_data=content_data)
        else:
            # 如果查無資料，顯示空的分類頁面
            return render_template('classTemplate.html', title=category_type.upper(), content_data=[])

    except Exception as e:
        app.logger.error(f"Error occurred while fetching content for category {category_type}: {e}")
        return "Internal Server Error", 500

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
        contents = transcribe_audio(converted_file_path)
        print("轉換完成")
        # print(contents[0])
        for i in range(len(contents[0])):
            if contents[0][i]['speakerId'] == "0":
                contentList.append("{}：{}".format("講者１", contents[0][i]['sentence']))
                print("{}：{}".format("講者１", contents[0][i]['sentence']))
            else:
                contentList.append("{}：{}".format("講者２", contents[0][i]['sentence']))
                print("{}：{}".format("講者２", contents[0][i]['sentence']))
  
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