from openai import AzureOpenAI
import sqlite3
import json
import re
import os

def ClosingReportOutput(chatContent: str, DATABASE_PATH: str = "database.db"):
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
                    "text": "我現在會給你一位被照顧的老人和安養中心社工的對話，請你照著步驟做\n\n第一步驟:\n    請把被照護的老人當成\"案主\"，而安養中心社工是\"本人\"，重新生成\n\n第二步驟:\n    將輸入內容修改依照[身]、[心]、[社會]、[其他]四大類從對話格式分成敘述性內容，並依照時間進行排序，其中身的部分重點強調關於身體狀況的內容，心的部分強調心理狀態內容，社會的部分強調關於活動及與家人朋友互動的內容，若標題為[特殊]，則直接將輸入內容整理成順暢的句子\n\n※注意事項:\n\n1.如果我提供的資料內容[身][心][社會][其他]四大類中，如果有些日期沒有內容或沒有日期，則空白，請依照我傳給你的內容進行整理，不要生成我沒有傳的內容\n\n2.不要用\"不錯、可能、也許\"這種模糊字眼，用直接的描述\n\n3.\"身\"的部分加強食慾吃飯相關內容也可以列出來，不要忽略\n例如:\"案主今天說想吃紅燒肉\"\n\n4.如果有分類是沒有內容的可以空白，但要有[身]、[心]、[社會]、[其他]這樣的大標題\n\n5.如對案主的身心健康和人際互動及餐與活動無關的(謝謝你，陳小姐，你也辛苦了。明天見！/明天見，呂伯伯！祝你有個美好的夜晚。/好的，謝謝你，陳小姐。祝我們都有一個美好的新年！)，都不需要保留\n\n舉例\n這是我會輸入的內容:\n[\n2024/11/19/09:26-大廳\n身:\n呂小姐：方太太，早安！今天感覺怎麼樣呢？昨晚睡得還好嗎？\n方太太：早安，呂小姐！昨晚睡得還不錯，只是半夜有醒來一次。不過，之後又很快睡著了。\n呂小姐：那就好，睡眠對健康很重要。最近膝蓋還有沒有不舒服呢？\n方太太：膝蓋偶爾還是會有點痛，特別是下樓梯的時候。不過，最近復健師教我的一些運動好像有幫助。\n呂小姐：太好了！持續做那些運動應該會有更好的效果。如果有需要，我們可以安排復健師再來看看。\n方太太：好啊，謝謝你們的關心。這裡的服務真的很周到。\n社會:\n呂小姐：不客氣！我們就是希望大家能在這裡住得舒適。對了，這週末社區會有一個手工藝活動，您有興趣參加嗎？\n方太太：聽起來不錯，我喜歡做手工藝。上次的插花活動我也很喜歡。\n呂小姐：太好了，我會幫您報名。這些活動不僅能動手，還能和其他住戶多交流，對身心都有好處。\n方太太：是啊，和大家一起活動感覺很開心。最近我女兒也有來看我，帶了孫子來，真是讓我開心了一整天。\n呂小姐：那真是太好了！家人的探望對情緒真的有很大的幫助。您看起來心情很好，這樣我也替您高興。\n其他:\n方太太：謝謝你，呂小姐。你總是這麼關心我們，真的很感激。\n呂小姐：這是我的工作，也是我的榮幸。您有任何需要隨時告訴我，好嗎？\n方太太：好的，謝謝你。\n \n2024/11/23/11:25-食堂\n身:\n呂小姐：方太太，您好！今天怎麼沒看到您吃早餐呢？\n方太太：呂小姐，早安。我今天早上有點不舒服，肚子一直咕嚕咕嚕的，感覺有點拉肚子，所以沒什麼食慾。\n呂小姐：哦，那可不太好。您昨天吃了什麼特別的東西嗎？\n方太太：也沒什麼特別的，就是平常的三餐。可能是昨晚的魚湯有點不太合胃口吧。\n呂小姐：了解。今天先喝點溫開水，讓胃腸休息一下。我們這裡的護士可以幫您檢查一下，看看是不是需要吃點藥。\n方太太：好，謝謝你。這樣的話，我就麻煩護士了。\n心:\n呂小姐：不麻煩，這是我們應該做的。方太太，您最近心情還好嗎？有沒有什麼需要我幫忙的？\n方太太：心情還好，就是這幾天胃口不好，心裡有點煩。希望快點好起來，這樣就能參加週末的手工藝活動了。\n呂小姐：我明白，生病總是讓人心情不太好。不過，您平時心情都很開朗，相信很快就會好起來的。這幾天我會多來看看您，有需要隨時告訴我。\n方太太：謝謝你，呂小姐。你的關心讓我覺得好多了。\n其他:\n呂小姐：不客氣，方太太。您一定要多休息，有什麼問題隨時找我或護士。\n方太太：好的，謝謝你。\n\n \n2024/11/26/15:23-大廳\n身:\n呂小姐：方太太，您好！昨天去看醫生了嗎？情況怎麼樣？\n方太太：呂小姐，早安。是的，昨天去了醫院。醫生說我只是腸胃有點不適，開了一些藥給我，讓我多休息。\n呂小姐：那就好，有醫生的指導，應該很快就會好起來的。您今天感覺怎麼樣？有沒有好一點？\n方太太：今天感覺好多了，肚子不再那麼不舒服了。只是還是有點沒胃口，但至少不像前幾天那麼難受。\n呂小姐：太好了，慢慢來，恢復需要一點時間。這幾天還是要注意飲食，吃些清淡的食物，讓腸胃慢慢適應\n方太太：嗯，我會注意的。謝謝你的關心，呂小姐。\n社會:\n呂小姐：不客氣，這是我應該做的。對了，這週末的手工藝活動還是會舉行，您覺得有體力參加嗎？\n方太太：我很想參加，不過可能要看看那天的狀況。如果還是不舒服，我就不去了。\n呂小姐：好的，您先好好休息，健康最重要。如果有需要，我可以幫您準備一些活動材料，讓您在房間裡也能輕鬆做。\n其他:\n方太太：那真是太好了，謝謝你，呂小姐。你總是這麼貼心。\n呂小姐：這是我的榮幸。您有任何需要或不舒服，隨時告訴我，好嗎？\n方太太：好的，謝謝你。\n \n 2024/12/20/08:56-食堂\n身:\n呂小姐：方太太，您好！好久不見，最近感覺怎麼樣？\n方太太：呂小姐，早安！最近好多了，謝謝你的關心。之前的腸胃問題已經完全好了，現在食慾也恢復了。\n社會:\n呂小姐：太好了，聽到您恢復健康我很高興。這段時間有沒有參加什麼活動呢？\n方太太：有啊，上次的手工藝活動我參加了，還做了一個聖誕花圈。這裡的活動總是讓我感覺很開心。\n呂小姐：那真不錯！聖誕節快到了，我們這裡也會舉辦一些慶祝活動，您有沒有興趣參加？\n方太太：當然有興趣，這些活動讓我覺得自己還是很有活力，能和大家一起過節很開心。\n呂小姐：太好了，我會幫您留意活動的安排，確保您不會錯過任何有趣的部分。對了，最近有沒有家人來探望您？\n方太太：有的，上週末我兒子來看我，我們還一起去附近的公園散步，聊了很多。\n呂小姐：聽起來很不錯，家人的陪伴真的很重要。方太太，您最近的心情也不錯吧？\n方太太：是的，心情很好。感覺生活充實，身體也健康了，真是很感謝大家的照顧。\n呂小姐：您能這麼說，我們也很開心。以後有任何需要或想參加的活動，隨時告訴我哦。\n方太太：好的，謝謝你，呂小姐。\n\n2025/01/10/13:08-大廳\n身:\n呂小姐：方太太，您好！新年快樂！跨年過得怎麼樣？\n方太太：呂小姐，新年快樂！我過得非常愉快。今年跨年，我的女兒帶我去她家一起慶祝，我們全家人聚在一起吃飯、聊天。\n呂小姐：聽起來很溫馨呢！有沒有什麼特別的活動或是慶祝方式？\n方太太：我們一起看了煙火，還玩了一些桌遊。孩子們還準備了一些小表演，讓我笑得合不攏嘴。\n呂小姐：那真是太好了！和家人在一起的時光總是特別珍貴。您有沒有許下新年的願望呢？\n方太太：有的，我希望新的一年大家都能健康平安，我也希望能多參加一些這裡的活動，保持活力。\n呂小姐：這是很棒的願望！我們這裡今年也會安排更多有趣的活動，讓您有更多機會參加。您有特別想參加的活動嗎？\n方太太：我聽說今年會有一些舞蹈課，我很想試試看。以前我很喜歡跳舞。\n呂小姐：太好了！我們一定會安排的。我會幫您留意，隨時通知您活動的時間。\n心:\n方太太：謝謝你，呂小姐。每次跟你聊完，我都覺得心情特別好。\n呂小姐：這是我的榮幸，方太太。希望今年我們能一起創造更多美好的回憶。\n方太太：一定會的，再次謝謝你。\n\n特殊:\n方太太最近看起來比較沒精神，可能是失眠的關係\n]\n\n我想要看到的結果\n\n### 身\n**2024/11/19**\n\u000b案主表示昨晚睡得不錯，但半夜醒來一次，之後很快再入睡。膝蓋偶爾在下樓梯時仍感到疼痛，但最近復健師教的運動有幫助，疼痛有所減輕。\n**2024/11/23\u000b**\n案主早上感到肚子不適，有拉肚子的情況，食慾不佳。她提到可能是昨晚的魚湯不合胃口，護士已協助檢查。\n**2024/11/26\u000b**\n案主前一天去醫院檢查，醫生診斷為腸胃不適，開了藥並建議多休息。她今天感覺情況好轉，但仍有些食慾不振。\n**2024/12/20\u000b**\n案主表示腸胃問題已完全康復，食慾恢復正常\n### 心\n**2024/11/23\u000b**\n案主因胃口不佳感到煩悶，希望能快點康復，參加週末的手工藝活動。社工的關心讓她感到心情有所緩解\n**2025/01/10\u000b**\n案主表示每次與社工聊天後心情都會變好，並感謝社工的支持與陪伴。她希望新的一年能創造更多美好回憶\n### 社會\n**2024/11/19\u000b**\n案主對安養中心的手工藝活動感興趣，並表示上次的插花活動讓她感到愉快。她提到最近女兒與孫子來探望她，讓她非常開心\n**2024/11/26**\n\u000b案主表示希望參加週末的手工藝活動，但會根據當天的身體狀況決定是否參加。社工表示可準備材料供她在房間內製作\n**2024/12/20\u000b**\n案主參加了手工藝活動，製作了一個聖誕花圈，感到非常開心。她提到上週末兒子來探望她，並一起去公園散步，心情愉快\n**2025/01/10\u000b**\n案主表示跨年時女兒帶她回家與家人團聚，一起吃飯、看煙火、玩桌遊，並觀看孩子們的表演。她希望新的一年能多參加活動，保持活力，並對即將安排的舞蹈課表達期待\n\n### 特殊:\n**2025/01/10**\n案主最近看起來比較沒精神，可能是失眠的關係\n"
                }
            ]
        }
    ]
    f = chatContent.split("\n")
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
    print("closing report output successful")
    return completion.choices[0].message.content