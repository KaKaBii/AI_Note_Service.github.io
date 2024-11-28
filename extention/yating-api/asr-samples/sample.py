import os
from ailabs_asr.streaming import StreamingClient #pip install ailabs_asr

# 獲取金鑰檔案
current_dir = os.path.dirname(os.path.abspath(__file__))
key_file_path = os.path.join(current_dir, 'key.txt')

if not os.path.exists(key_file_path):
    raise FileNotFoundError(f"檔案 '{key_file_path}' 不存在，請檢查檔案路徑或內容！")

# 繼續讀取金鑰
with open(key_file_path, 'r') as file:
    api_key = file.read().strip()
    #print(api_key)

def on_processing_sentence(message):
  print(f'hello: {message["asr_sentence"]}')

def on_final_sentence(message):
  print(f'world: {message["asr_sentence"]}')

#使用從 key.txt 讀取的金鑰初始化 StreamingClient
asr_client = StreamingClient(key=api_key)

# 獲取錄音檔
file_name = 'your-voice-file.wav'
record_file_path = os.path.join(current_dir, file_name)

# start Streaming with a wav file
asr_client.start_streaming_wav(
  pipeline='asr-zh-tw-std',
  # verbose=True,
  file=record_file_path, #remove 'file' to switch to streaming mode. 
  on_processing_sentence=on_processing_sentence,
  on_final_sentence=on_final_sentence
)


