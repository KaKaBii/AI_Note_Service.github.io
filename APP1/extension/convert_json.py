from openai import AzureOpenAI
import sqlite3
import json
import re
import os

def ConvertJSON(ClosingReport: str, DATABASE_PATH: str = "database.db"):
    api_version = "2024-02-15-preview"

    # gets the API Key from environment variable AZURE_OPENAI_API_KEY
    current_dir = os.getcwd()
    key_file_path = os.path.join(current_dir, 'gpt_key.txt')
    if not os.path.exists(key_file_path):
        raise FileNotFoundError(f"檔案 '{key_file_path}' 不存在，請檢查檔案路徑或內容！")

    with open(key_file_path, 'r') as file:
        api_key = file.read().strip()
        if api_key == "" or None:
            raise FileNotFoundError(f"金鑰為空！")
    client = AzureOpenAI(
        api_version=api_version,
        api_key=api_key,
        # https://learn.microsoft.com/en-us/azure/cognitive-services/openai/how-to/create-resource?pivots=web-portal#create-a-resource
        azure_endpoint="https://aidesign.openai.azure.com/",
    )
    messages = [
        {
            "role": "system",
            "content": [
                {
                    "type": "text",
                    "text": "將文本轉為Json格式，網頁開發要用。"
                }
            ]
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "身"
                },
                {
                    "type": "text",
                    "text": "2024/11/13"
                },
                {
                    "type": "text",
                    "text": "案主早上散步後感覺精神好多了，腰偶爾會痠，但比之前好多了。午餐時間食慾不錯，雖然有些東西咬起來不太方便，但還是吃得下。"
                },
                {
                    "type": "text",
                    "text": "\n"
                },
                {
                    "type": "text",
                    "text": "2024/11/18"
                },
                {
                    "type": "text",
                    "text": "案主在套圈圈活動中站久了腰有點不舒服，後來找了個椅子坐了一會兒，感覺好多了。"
                },
                {
                    "type": "text",
                    "text": "\n"
                },
                {
                    "type": "text",
                    "text": "2024/11/26"
                },
                {
                    "type": "text",
                    "text": "案主早上起得早，來食堂吃早餐，胃口不錯，選擇了粥和包子。"
                },
                {
                    "type": "text",
                    "text": "\n"
                },
                {
                    "type": "text",
                    "text": "心"
                },
                {
                    "type": "text",
                    "text": "2024/11/13"
                },
                {
                    "type": "text",
                    "text": "案主心情不錯，有時候會想念家人，但他們偶爾也會來看他。"
                },
                {
                    "type": "text",
                    "text": "\n"
                },
                {
                    "type": "text",
                    "text": "2024/11/18"
                },
                {
                    "type": "text",
                    "text": "案主打算把一個小綠色盆栽放在房間裡，讓它陪著自己。今天的活動讓他很開心。"
                },
                {
                    "type": "text",
                    "text": "\n"
                },
                {
                    "type": "text",
                    "text": "2024/11/26"
                },
                {
                    "type": "text",
                    "text": "案主接到老朋友的電話，聊起往事，心裡有些感慨，但聊完之後心裡暖暖的，像是重新找回了一些年輕時的熱情。"
                },
                {
                    "type": "text",
                    "text": "\n"
                },
                {
                    "type": "text",
                    "text": "2024/12/18"
                },
                {
                    "type": "text",
                    "text": "案主心情不錯，開始整理一些老照片，回憶起很多美好的時光。"
                },
                {
                    "type": "text",
                    "text": "\n"
                },
                {
                    "type": "text",
                    "text": "2024/12/27"
                },
                {
                    "type": "text",
                    "text": "案主心情特別好，因為快到年底了，總覺得有些期待。"
                },
                {
                    "type": "text",
                    "text": "\n"
                },
                {
                    "type": "text",
                    "text": "社會"
                },
                {
                    "type": "text",
                    "text": "2024/11/13"
                },
                {
                    "type": "text",
                    "text": "案主對週末社區的小型園遊會活動感興趣，喜歡熱鬧，可以和大家聊天。"
                },
                {
                    "type": "text",
                    "text": "\n"
                },
                {
                    "type": "text",
                    "text": "2024/11/18"
                },
                {
                    "type": "text",
                    "text": "案主參加了園遊會，玩了套圈圈的遊戲，贏了一個小獎品，感到非常開心。"
                },
                {
                    "type": "text",
                    "text": "\n"
                },
                {
                    "type": "text",
                    "text": "2024/11/26"
                },
                {
                    "type": "text",
                    "text": "案主和老朋友聯繫，聊起以前一起工作的時候，感到懷念和感慨時間過得真快。"
                },
                {
                    "type": "text",
                    "text": "\n"
                },
                {
                    "type": "text",
                    "text": "2024/12/18"
                },
                {
                    "type": "text",
                    "text": "案主打算去看看園子裡的新種冬季植物。"
                },
                {
                    "type": "text",
                    "text": "\n"
                },
                {
                    "type": "text",
                    "text": "2024/12/27"
                },
                {
                    "type": "text",
                    "text": "案主計劃參加社區的跨年活動，會有煙火表演和音樂會，並計劃和幾個老朋友聚一聚，大家一起吃飯，聊聊天，回顧這一年的事情。"
                },
                {
                    "type": "text",
                    "text": "\n"
                },
                {
                    "type": "text",
                    "text": "其他"
                }
            ]
        },
        {
            "role": "assistant",
            "content": [
                {
                    "type": "text",
                    "text": "```json\n{\n  \"身\": [\n    {\n      \"日期\": \"2024/11/13\",\n      \"描述\": \"案主早上散步後感覺精神好多了，腰偶爾會痠，但比之前好多了。午餐時間食慾不錯，雖然有些東西咬起來不太方便，但還是吃得下。\"\n    },\n    {\n      \"日期\": \"2024/11/18\",\n      \"描述\": \"案主在套圈圈活動中站久了腰有點不舒服，後來找了個椅子坐了一會兒，感覺好多了。\"\n    },\n    {\n      \"日期\": \"2024/11/26\",\n      \"描述\": \"案主早上起得早，來食堂吃早餐，胃口不錯，選擇了粥和包子。\"\n    }\n  ],\n  \"心\": [\n    {\n      \"日期\": \"2024/11/13\",\n      \"描述\": \"案主心情不錯，有時候會想念家人，但他們偶爾也會來看他。\"\n    },\n    {\n      \"日期\": \"2024/11/18\",\n      \"描述\": \"案主打算把一個小綠色盆栽放在房間裡，讓它陪著自己。今天的活動讓他很開心。\"\n    },\n    {\n      \"日期\": \"2024/11/26\",\n      \"描述\": \"案主接到老朋友的電話，聊起往事，心裡有些感慨，但聊完之後心裡暖暖的，像是重新找回了一些年輕時的熱情。\"\n    },\n    {\n      \"日期\": \"2024/12/18\",\n      \"描述\": \"案主心情不錯，開始整理一些老照片，回憶起很多美好的時光。\"\n    },\n    {\n      \"日期\": \"2024/12/27\",\n      \"描述\": \"案主心情特別好，因為快到年底了，總覺得有些期待。\"\n    }\n  ],\n  \"社會\": [\n    {\n      \"日期\": \"2024/11/13\",\n      \"描述\": \"案主對週末社區的小型園遊會活動感興趣，喜歡熱鬧，可以和大家聊天。\"\n    },\n    {\n      \"日期\": \"2024/11/18\",\n      \"描述\": \"案主參加了園遊會，玩了套圈圈的遊戲，贏了一個小獎品，感到非常開心。\"\n    },\n    {\n      \"日期\": \"2024/11/26\",\n      \"描述\": \"案主和老朋友聯繫，聊起以前一起工作的時候，感到懷念和感慨時間過得真快。\"\n    },\n    {\n      \"日期\": \"2024/12/18\",\n      \"描述\": \"案主打算去看看園子裡的新種冬季植物。\"\n    },\n    {\n      \"日期\": \"2024/12/27\",\n      \"描述\": \"案主計劃參加社區的跨年活動，會有煙火表演和音樂會，並計劃和幾個老朋友聚一聚，大家一起吃飯，聊聊天，回顧這一年的事情。\"\n    }\n  ]\n}\n```"
                }
            ]
        }
    ]
    f = ClosingReport.split("\n")
    for prompt in f:
        messages.append({
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": prompt,
                }
            ],
        })
    completion = client.chat.completions.create(
        model="AI_Design_Pro",  # e.g. gpt-35-instant
        messages=messages,
        temperature=0.1,
        top_p=0.1,
        max_tokens=4096
    )
    print("convert json successful")
    return json.loads(re.split("json\n", re.split("```", completion.choices[0].message.content)[1])[1])