import os
from pydub import AudioSegment
from ailabs_asr.streaming import StreamingClient #pip install ailabs-asr

# 獲取金鑰檔案
current_dir = os.path.dirname(os.path.abspath(__file__))
key_file_path = os.path.join(current_dir, 'key.txt')

if not os.path.exists(key_file_path):
    raise FileNotFoundError(f"檔案 '{key_file_path}' 不存在，請檢查檔案路徑或內容！")

# 繼續讀取金鑰
with open(key_file_path, 'r') as file:
    api_key = file.read().strip()
    #api_key = "asdfghjk"
    #print(api_key)

contents = []

def on_processing_sentence(message):
  print(f'{message["asr_sentence"]}')
  

def on_final_sentence(message):
  contents.append(message["asr_sentence"])  # 直接訪問全局變量
  #print(f'{message["asr_sentence"]}')

def ensure_audio_format(input_file_path, output_file_path):
    """
    將音頻文件轉換為指定的格式：
    16kHz, 單聲道, 16 bits per sample, PCM 格式
    """
    try:
        # 從文件中加載音頻
        audio = AudioSegment.from_file(input_file_path)

        # 設置音頻參數：16kHz 采樣率、單聲道、16位深度
        audio = audio.set_frame_rate(16000)
        audio = audio.set_channels(1)
        audio = audio.set_sample_width(2)  # 16 bits -> 2 bytes

        # 將文件導出為符合要求的 PCM WAV 文件
        audio.export(output_file_path, format="wav")
        
        print(f"音頻已成功轉換並保存至：{output_file_path}")

    except Exception as e:
        print(f"音頻格式處理失敗：{e}")

#使用從 key.txt 讀取的金鑰初始化 StreamingClient
asr_client = StreamingClient(key=api_key)

# 獲取錄音檔
file_name = '60s.wav'
record_file_path = os.path.join(current_dir, file_name)

output_file_path = os.path.splitext(record_file_path)[0] + ".wav"
ensure_audio_format(record_file_path, output_file_path)


# start streaming with wav file
asr_client.start_streaming_wav(
  pipeline='asr-zh-tw-std',
  file=record_file_path,
  verbose=False, # enable verbose to show detailed recognition result
  #on_processing_sentence=on_processing_sentence,
  on_final_sentence=on_final_sentence
)

# without file to start streaming with the computer's microphone
# asr_client.start_streaming_wav(
#   pipeline='asr-zh-tw-std',
#   on_processing_sentence=on_processing_sentence,
#   on_final_sentence=on_final_sentence
# )

for index, content in enumerate(contents):
   print(index, content)