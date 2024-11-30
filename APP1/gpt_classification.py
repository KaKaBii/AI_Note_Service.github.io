from openai import AzureOpenAI
import sqlite3
import json
import re
import os

def GPT_classification(DATABASE_PATH="database.db", sql_command="SELECT name, content FROM transcripts ORDER BY timestamp DESC LIMIT 1"):
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
                    "text": "請依照以下規則將給定的對話內容進行分類，並生成一份分類文檔。分類包括四大類別：身、心、社會和其他。請確保對話的連貫性，不跳過任何一句話，並使用分隔號分開不同段落。  \n   \n**分類規則：**  \n   \n1. **身**：  \n    - 包括食慾、身體健康（如膝蓋痛、腰痛、行動不便、覺得冷等）、睡眠安穩的情形。  \n    - 例如：  \n        \"- 陳小姐: 呂伯伯，早上好！沒想到這麼早就能在食堂遇見您。 \" \n        \"- 呂伯伯: 早啊，陳小姐！今天起得早，想來這裡吃個豐盛的早餐。 \"\n   \n2. **心**：  \n    - 包括情緒方面（如憂鬱、開心、心智狀況等）。  \n    - 例如：  \n        \"- 呂小姐：「是啊，身體的變化我們要多注意。對了，最近心情怎麼樣？有沒有覺得比較輕鬆一點？」\"\n        \"- 張太太：「還可以啦，不過有時候會想起以前的事情，心裡難免有點感慨。前幾天夢到我老伴，醒來後心裡空空的，覺得有點孤單。」\"  \n   \n3. **社會**：  \n    - 包括老人的社交、社區舉辦的活動、家人探望、和朋友的互動、打電話等。  \n    - 例如：  \n        \"- 社工（小張）： 這樣很好呢，適當的運動對身體很有幫助。上次您提到想和家人一起去公園，聽說他們前幾天來看您了，怎麼樣，有沒有一起出去走走？\"  \n        \"- 劉伯伯： 有的，他們帶我去附近的公園轉了一圈，還在那邊的小茶館喝了茶，聊了好多事情，真開心。\"  \n   \n4. **其他**：  \n    - 若對話中有不屬於“身”、“心”、“社會”三大分類的對話則歸類在此。  \n    - 例如：  \n        \"- 陳小姐: 哇，整理老照片一定勾起了很多回憶吧！有沒有什麼特別有趣的故事可以分享？\"  \n        \"- 呂伯伯: 是啊，看到年輕時候的照片，想起了很多有趣的事情。有一張是我們一起去爬山，那次我們還迷了路，結果在山上過了一夜。\"  \n------------------------------------------------------------------------------------------\n   \n**注意事項：**  \n- 確保每段對話只在一個分類中出現。  \n- 保持對話的連貫性，不跳過任何一句話。  \n- 使用分隔號（——）分開不同段落。  \n-如遇不知道如何分類的情況，就先分類在其他。\n-切記也不要把範例中的對話生成出來，那只是你的參考資料。\n-\"\"裡的文字就是參考範例。\n   --------------------------------------------------------------------------------------\n**其餘範例-參考資料：**  \n   \n**身:**  \n\"陳小姐: 呂伯伯，早上好！沒想到這麼早就能在食堂遇見您。\"  \n\"呂伯伯: 早啊，陳小姐！今天起得早，想來這裡吃個豐盛的早餐。\"  \n\"陳小姐: 看來您的胃口不錯呀！今天早餐有什麼特別想吃的嗎？\"  \n\"呂伯伯: 我看到有粥和包子，就拿了一些。早上吃點熱的，感覺整個人都暖和起來了。\"  \n\"陳小姐: 是啊，早上的粥最能暖胃了。\"  \n\"呂伯伯: 是啊，心情好，吃飯也香。今天的包子特別好吃，你也試試吧。\"  \n   \n**心:**  \n\"陳小姐: 對了，呂伯伯，您最近心情怎麼樣？\"  \n\"呂伯伯: 最近心情還不錯，只是昨天接到一個老朋友的電話，聊起了一些往事，心裡有些感慨。\"  \n——  \n\"陳小姐: 那真是太好了。保持這種心情，對身體和生活都有很大的幫助呢。\"  \n   \n**社會:**  \n\"陳小姐: 原來如此，老朋友的聯繫總是讓人感觸良多。是什麼樣的往事呢？\"  \n\"呂伯伯: 我們聊到了以前一起工作的時候，想起那時候一起努力的日子，真是懷念啊。也有點感慨時間過得真快。\"  \n\"陳小姐: 是啊，回憶總是美好的。能夠和老朋友敘舊，也是很珍貴的事情呢。\"  \n\"呂伯伯: 沒錯，聊完之後，我也覺得心裡暖暖的，像是重新找回了一些年輕時的熱情。\"  \n   \n**其他:**  \n\"陳小姐: 好的，我也去拿一個嘗嘗。希望您今天也有個愉快的開始！\"  \n\"呂伯伯: 謝謝你，陳小姐。希望你今天也順順利利的！我們等會兒再聊。\"  \n\"陳小姐: 好的，呂伯伯，等會兒見！'  \n   \n---  \n   \n請使用以上提示詞來進行對話內容的分類。\n最後請將結果轉為Json格式，網頁開發要用。\n"
                }
            ]
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "\n"
                },
                {
                    "type": "text",
                    "text": "呂小姐：方太太，您好！今天怎麼沒看到您吃早餐呢？"
                },
                {
                    "type": "text",
                    "text": "方太太：呂小姐，早安。我今天早上有點不舒服，肚子一直咕嚕咕嚕的，感覺有點拉肚子，所以沒什麼食慾。"
                },
                {
                    "type": "text",
                    "text": "呂小姐：哦，那可不太好。您昨天吃了什麼特別的東西嗎？"
                },
                {
                    "type": "text",
                    "text": "方太太：也沒什麼特別的，就是平常的三餐。可能是昨晚的魚湯有點不太合胃口吧。"
                },
                {
                    "type": "text",
                    "text": "呂小姐：了解。今天先喝點溫開水，讓胃腸休息一下。我們這裡的護士可以幫您檢查一下，看看是不是需要吃點藥。"
                },
                {
                    "type": "text",
                    "text": "方太太：好，謝謝你。這樣的話，我就麻煩護士了。"
                },
                {
                    "type": "text",
                    "text": "呂小姐：不麻煩，這是我們應該做的。方太太，您最近心情還好嗎？有沒有什麼需要我幫忙的？"
                },
                {
                    "type": "text",
                    "text": "方太太：心情還好，就是這幾天胃口不好，心裡有點煩。希望快點好起來，這樣就能參加週末的手工藝活動了。"
                },
                {
                    "type": "text",
                    "text": "呂小姐：我明白，生病總是讓人心情不太好。不過，您平時心情都很開朗，相信很快就會好起來的。這幾天我會多來看看您，有需要隨時告訴我。"
                },
                {
                    "type": "text",
                    "text": "方太太：謝謝你，呂小姐。你的關心讓我覺得好多了。"
                },
                {
                    "type": "text",
                    "text": "呂小姐：不客氣，方太太。您一定要多休息，有什麼問題隨時找我或護士。"
                },
                {
                    "type": "text",
                    "text": "方太太：好的，謝謝你。"
                },
                {
                    "type": "text",
                    "text": "\n"
                },
                {
                    "type": "text",
                    "text": "\n"
                }
            ]
        },
        {
            "role": "assistant",
            "content": [
                {
                    "type": "text",
                    "text": "```json\n{\n  \"身\": [\n    \"呂小姐１：方太太，您好！今天怎麼沒看到您吃早餐呢？\",\n    \"方太太１：呂小姐，早安。我今天早上有點不舒服，肚子一直咕嚕咕嚕的，感覺有點拉肚子，所以沒什麼食慾。\",\n    \"呂小姐２：哦，那可不太好。您昨天吃了什麼特別的東西嗎？\",\n    \"方太太２：也沒什麼特別的，就是平常的三餐。可能是昨晚的魚湯有點不太合胃口吧。\",\n    \"呂小姐３：了解。今天先喝點溫開水，讓胃腸休息一下。我們這裡的護士可以幫您檢查一下，看看是不是需要吃點藥。\",\n    \"方太太３：好，謝謝你。這樣的話，我就麻煩護士了。\",\n    \"呂小姐４：不麻煩，這是我們應該做的。\"\n  ],\n  \"心\": [\n    \"呂小姐１：方太太，您最近心情還好嗎？有沒有什麼需要我幫忙的？\",\n    \"方太太１：心情還好，就是這幾天胃口不好，心裡有點煩。希望快點好起來，這樣就能參加週末的手工藝活動了。\",\n    \"呂小姐２：我明白，生病總是讓人心情不太好。不過，您平時心情都很開朗，相信很快就會好起來的。這幾天我會多來看看您，有需要隨時告訴我。\",\n    \"方太太２：謝謝你，呂小姐。你的關心讓我覺得好多了。\"\n  ],\n  \"社會\": [],\n  \"其他\": [\n    \"呂小姐１：不客氣，方太太。您一定要多休息，有什麼問題隨時找我或護士。\",\n    \"方太太１：好的，謝謝你。\"\n  ]\n}\n```"
                }
            ]
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "2024/11/18/10:37-大廳"
                },
                {
                    "type": "text",
                    "text": "**呂小姐**：郭伯伯，早安！今天感覺怎麼樣？"
                },
                {
                    "type": "text",
                    "text": "**郭伯伯**：早安，呂小姐。嗯，我今天還不錯，只是早上起來膝蓋有點酸。"
                },
                {
                    "type": "text",
                    "text": "**呂小姐**：哦，膝蓋酸痛啊，那吃早餐的時候食慾還好嗎？"
                },
                {
                    "type": "text",
                    "text": "**郭伯伯**：早餐還行，我喜歡今天的稀飯，不過吃得不多。"
                },
                {
                    "type": "text",
                    "text": "**呂小姐**：好的，我會跟護理人員說一下，看看有沒有什麼可以幫你舒緩膝蓋的。昨晚睡得怎麼樣？"
                },
                {
                    "type": "text",
                    "text": "**郭伯伯**：昨晚睡得不太好，半夜醒來好幾次。"
                },
                {
                    "type": "text",
                    "text": "**呂小姐**：了解，那我們等一下可以去散步，看看能不能讓你晚上睡得更好。最近有沒有覺得心情怎麼樣？"
                },
                {
                    "type": "text",
                    "text": "**郭伯伯**：嗯，有時候會忘記一些事情，心裡有點煩，不過看到你們來陪我，心情就好多了。"
                },
                {
                    "type": "text",
                    "text": "**呂小姐**：郭伯伯，您很棒，能夠這麼坦然面對。對了，最近有參加什麼活動嗎？或者家裡有誰來看您？"
                },
                {
                    "type": "text",
                    "text": "**郭伯伯**：上次女兒來看我，帶了孫子來，我們一起玩得很開心。活動嘛，我記得上週有個唱歌活動，我還跟著哼了幾句。"
                },
                {
                    "type": "text",
                    "text": "**呂小姐**：太好了！保持這樣的心情很重要。那我們等一下去院子走走，然後我再幫你安排一些您喜歡的活動，好嗎？"
                },
                {
                    "type": "text",
                    "text": "**郭伯伯**：好啊，謝謝你，呂小姐。"
                },
                {
                    "type": "text",
                    "text": "**呂小姐**：不客氣，郭伯伯，能陪您聊天我也很開心。"
                },
                {
                    "type": "text",
                    "text": "\n"
                },
                {
                    "type": "text",
                    "text": "\n"
                },
                {
                    "type": "text",
                    "text": "\n"
                },
                {
                    "type": "text",
                    "text": "\n"
                }
            ]
        },
        {
            "role": "assistant",
            "content": [
                {
                    "type": "text",
                    "text": "```json\n{\n  \"身\": [\n    \"呂小姐１：郭伯伯，早安！今天感覺怎麼樣？\",\n    \"郭伯伯１：早安，呂小姐。嗯，我今天還不錯，只是早上起來膝蓋有點酸。\",\n    \"呂小姐２：哦，膝蓋酸痛啊，那吃早餐的時候食慾還好嗎？\",\n    \"郭伯伯２：早餐還行，我喜歡今天的稀飯，不過吃得不多。\",\n    \"呂小姐３：好的，我會跟護理人員說一下，看看有沒有什麼可以幫你舒緩膝蓋的。昨晚睡得怎麼樣？\",\n    \"郭伯伯３：昨晚睡得不太好，半夜醒來好幾次。\",\n    \"呂小姐４：了解，那我們等一下可以去散步，看看能不能讓你晚上睡得更好。\"\n  ],\n  \"心\": [\n    \"呂小姐１：最近有沒有覺得心情怎麼樣？\",\n    \"郭伯伯１：嗯，有時候會忘記一些事情，心裡有點煩，不過看到你們來陪我，心情就好多了。\",\n    \"呂小姐２：郭伯伯，您很棒，能夠這麼坦然面對。\"\n  ],\n  \"社會\": [\n    \"呂小姐１：對了，最近有參加什麼活動嗎？或者家裡有誰來看您？\",\n    \"郭伯伯１：上次女兒來看我，帶了孫子來，我們一起玩得很開心。活動嘛，我記得上週有個唱歌活動，我還跟著哼了幾句。\",\n    \"呂小姐２：太好了！保持這樣的心情很重要。那我們等一下去院子走走，然後我再幫你安排一些您喜歡的活動，好嗎？\",\n    \"郭伯伯２：好啊，謝謝你，呂小姐。\"\n  ],\n  \"其他\": [\n    \"呂小姐１：不客氣，郭伯伯，能陪您聊天我也很開心。\"\n  ]\n}\n```"
                }
            ]
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "我今天吃牛肉麵，心情還不錯，等等要上台報告"
                }
            ]
        },
        {
            "role": "assistant",
            "content": [
                {
                    "type": "text",
                    "text": "```json\n{\n  \"身\": [\n    \"講者１：我今天吃牛肉麵\"\n  ],\n  \"心\": [\n    \"講者１：心情還不錯\"\n  ],\n  \"社會\": [\n    \"講者１：等等要上台報告\"\n  ],\n  \"其他\": []\n}\n```"
                }
            ]
        }
    ]
    rows = ""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute(sql_command)
        rows = cursor.fetchall()[0]
        conn.commit()
        conn.close()
    except Exception as e: print(e)
    f = rows[1].split("\n")
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
        max_tokens=1200
    )
    print("GPT classification successful")
    return rows[0], json.loads(re.split("json\n", re.split("```", completion.choices[0].message.content)[1])[1])