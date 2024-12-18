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
                    "text": "我現在會給你一位被照顧的老人和安養中心社工的對話，請你照著步驟做\n\n第一步驟:\n\n請把被照護的老人當成\"案主\"，而安養中心社工是\"本人\"，重新生成\n\n第二步驟:\n\n將上述內容修改依照身、心、社會、其他四大類分成簡單敘述性內容，並依照時間進行排序，其中身的部分重點強調關於身體狀況的內容，心的部分強調親情狀態內容，社會的部分\n強調關於活動及與家人朋友互動的內容，其他的內容則是關於特殊活動，不屬於\"身、心、社會\"的紀錄，不要用對話形式逐字呈現而是以文本的形式總結生成出來。\n\n\n※注意事項:\n\n1.如果我提供的資料內容身心社會四大類中，其中如果有些日期沒有內容或沒有日期，則空白，不要無中生有憑空想像，\n不要有這種沒有資料的生成內容:\n例如:\n\"2024/12/27-案主今天心情特別好，因為快到年底了，總覺得有些期待。\"但社工和案主的對話根本就沒有出現過，所以不可以自己胡亂生成。\n\n2.不要用\"不錯、可能、也許\"這種模糊字眼，用直接的描述\n\n3.\"身\"的部分加強食慾吃飯相關內容也可以把出來，不要忽略\n例如:\"案主今天說想吃紅燒肉\"\n\n4.如果有分類是沒有內容的可以空白，但要有像身、心、社會、其他一樣的大標題\n\n5.如對案主的身心健康和人際互動及餐與活動無關的(謝謝你，陳小姐，你也辛苦了。明天見！/明天見，呂伯伯！祝你有個美好的夜晚。/好的，謝謝你，陳小姐。祝我們都有一個美好的新年！)，都不需要保留\n\n6.其他的分類中如果沒有內容，就不用顯示日期\n\n\n\n"
                }
            ]
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "呂伯伯"
                },
                {
                    "type": "text",
                    "text": "\n"
                },
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
                    "text": "陳小姐: 呂伯伯，早安啊！剛剛去散步啦？今天天氣不錯哦，適合出門走走。"
                },
                {
                    "type": "text",
                    "text": "呂伯伯: 是啊，今天天氣很好，走了一圈感覺精神好多了。"
                },
                {
                    "type": "text",
                    "text": "陳小姐: 真好！散步對身體很有幫助哦。最近腰還好嗎？有沒有不舒服的地方？"
                },
                {
                    "type": "text",
                    "text": "呂伯伯: 腰還是偶爾會痠，不過比之前好多了。"
                },
                {
                    "type": "text",
                    "text": "陳小姐: 那就好，有什麼不舒服的地方一定要告訴我們哦。午餐時間快到了，最近食慾怎麼樣？"
                },
                {
                    "type": "text",
                    "text": "呂伯伯: 食慾還不錯，雖然有些東西咬起來不太方便，但還是吃得下。"
                },
                {
                    "type": "text",
                    "text": "2024/11/18"
                },
                {
                    "type": "text",
                    "text": "呂伯伯: 其實我今天主要就是在套圈圈那裡待了很久，看到大家玩得開心，我也忍不住多試了幾次。不過，站久了我的腰有點不舒服。"
                },
                {
                    "type": "text",
                    "text": "陳小姐: 哎呀，那可要注意休息哦。要不要我幫你找個地方坐下來休息一下？"
                },
                {
                    "type": "text",
                    "text": "呂伯伯: 謝謝你，我剛剛已經找了個椅子坐了一會兒，現在感覺好多了。"
                },
                {
                    "type": "text",
                    "text": "陳小姐: 那就好，如果腰還是不舒服，記得告訴我，我們可以安排按摩或熱敷幫助舒緩。"
                },
                {
                    "type": "text",
                    "text": "\n"
                },
                {
                    "type": "text",
                    "text": "呂伯伯: 是該休息一下了，玩了一整天，現在覺得有點累。"
                },
                {
                    "type": "text",
                    "text": "陳小姐: 那就好好休息吧，有什麼需要隨時告訴我哦。希望你今晚睡個好覺！"
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
                },
                {
                    "type": "text",
                    "text": "2024/11/26"
                },
                {
                    "type": "text",
                    "text": "陳小姐: 呂伯伯，早上好！沒想到這麼早就能在食堂遇見您。"
                },
                {
                    "type": "text",
                    "text": "呂伯伯: 早啊，陳小姐！今天起得早，想來這裡吃個豐盛的早餐。"
                },
                {
                    "type": "text",
                    "text": "陳小姐: 看來您的胃口不錯呀！今天早餐有什麼特別想吃的嗎？"
                },
                {
                    "type": "text",
                    "text": "呂伯伯: 我看到有粥和包子，就拿了一些。早上吃點熱的，感覺整個人都暖和起來了。"
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
                    "text": "陳小姐: 如果有什麼需要調整的，隨時告訴我哦。我們也可以幫你看看有沒有什麼適合的食物。最近心情怎麼樣？"
                },
                {
                    "type": "text",
                    "text": "呂伯伯: 心情還不錯，有時候會想念家人，但他們偶爾也會來看我。"
                },
                {
                    "type": "text",
                    "text": "2024/11/18"
                },
                {
                    "type": "text",
                    "text": "呂伯伯: 是一個小小的綠色盆栽，我打算放在房間裡，讓它陪著我。"
                },
                {
                    "type": "text",
                    "text": "陳小姐: 這樣很好啊，有了小盆栽，房間也會多一點生氣呢。除了套圈圈，還有沒有其他有趣的事情發生？"
                },
                {
                    "type": "text",
                    "text": "\n"
                },
                {
                    "type": "text",
                    "text": "呂伯伯: 好的，我會注意的。今天的活動真的很開心，謝謝你們的精心安排。"
                },
                {
                    "type": "text",
                    "text": "陳小姐: 不客氣，只要你們開心，我們就很滿足了。那你晚上有什麼計劃嗎？要不要早點休息？"
                },
                {
                    "type": "text",
                    "text": "2024/11/26"
                },
                {
                    "type": "text",
                    "text": "陳小姐: 是啊，早上的粥最能暖胃了。對了，呂伯伯，您最近心情怎麼樣？"
                },
                {
                    "type": "text",
                    "text": "呂伯伯: 最近心情還不錯，只是昨天接到一個老朋友的電話，聊起了一些往事，心裡有些感慨。"
                },
                {
                    "type": "text",
                    "text": "\n"
                },
                {
                    "type": "text",
                    "text": "呂伯伯: 沒錯，聊完之後，我也覺得心裡暖暖的，像是重新找回了一些年輕時的熱情。"
                },
                {
                    "type": "text",
                    "text": "陳小姐: 那真是太好了。保持這種心情，對身體和生活都有很大的幫助呢。"
                },
                {
                    "type": "text",
                    "text": "呂伯伯: 是啊，心情好，吃飯也香。今天的包子特別好吃，你也試試吧。"
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
                    "text": "陳小姐: 那聽起來很不錯呢，冬季的植物也別有一番風味。對了，最近心情怎麼樣？"
                },
                {
                    "type": "text",
                    "text": "呂伯伯: 最近心情不錯，上次和老朋友聊完之後，我也開始整理一些老照片，回憶起很多美好的時光。"
                },
                {
                    "type": "text",
                    "text": "\n"
                },
                {
                    "type": "text",
                    "text": "陳小姐: 聽您這麼說，我都能感受到那種冒險的樂趣了。保持這種愉快的心情，生活也會更加美好。"
                },
                {
                    "type": "text",
                    "text": "呂伯伯: 謝謝你，陳小姐。和你聊聊天，我也覺得心情更好了。"
                },
                {
                    "type": "text",
                    "text": "陳小姐: 不客氣，呂伯伯。希望您今天有個愉快的一天！如果有什麼需要，隨時告訴我哦。"
                },
                {
                    "type": "text",
                    "text": "2024/12/27"
                },
                {
                    "type": "text",
                    "text": "陳小姐: 呂伯伯，早上好！今天感覺怎麼樣？"
                },
                {
                    "type": "text",
                    "text": "呂伯伯: 早上好，陳小姐！今天心情特別好，因為快到年底了，總覺得有些期待。"
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
                    "text": "陳小姐: 家人來看你一定很開心吧！這週末社區有個小活動，你有興趣參加嗎？"
                },
                {
                    "type": "text",
                    "text": "呂伯伯: 蛤，是甚麼活動啊?"
                },
                {
                    "type": "text",
                    "text": "陳小姐: 這週末我們會舉辦一個小型的園遊會活動，地點就在中心的花園裡。到時候會有一些攤位遊戲、音樂表演，還有手工藝品展示。大家可以一起來參加，享受一下熱鬧的氣氛，也可以試試看不同的小吃哦。"
                },
                {
                    "type": "text",
                    "text": "\n"
                },
                {
                    "type": "text",
                    "text": "呂伯伯: 聽起來很有趣呢！我最喜歡熱鬧了，我也可以和大家聊天。"
                },
                {
                    "type": "text",
                    "text": "\n"
                },
                {
                    "type": "text",
                    "text": "陳小姐: 是啊，這樣的活動也是一個認識新朋友的好機會。如果你有什麼想試試看的遊戲或活動，可以告訴我，我幫你安排。"
                },
                {
                    "type": "text",
                    "text": "2024/11/18"
                },
                {
                    "type": "text",
                    "text": "陳小姐: 呂伯伯，下午好！今天的園遊會玩得怎麼樣啊？"
                },
                {
                    "type": "text",
                    "text": "呂伯伯: 哎呀，陳小姐，今天真是太開心了！我參加了一個套圈圈的遊戲，居然還贏了一個小獎品呢！"
                },
                {
                    "type": "text",
                    "text": "2024/11/26"
                },
                {
                    "type": "text",
                    "text": "陳小姐: 原來如此，老朋友的聯繫總是讓人感觸良多。是什麼樣的往事呢？"
                },
                {
                    "type": "text",
                    "text": "呂伯伯: 我們聊到了以前一起工作的時候，想起那時候一起努力的日子，真是懷念啊。也有點感慨時間過得真快。"
                },
                {
                    "type": "text",
                    "text": "陳小姐: 是啊，回憶總是美好的。能夠和老朋友敘舊，也是很珍貴的事情呢。"
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
                    "text": "陳小姐: 做得對！有時候天氣變化太快，身體容易不適應。今天有什麼特別的計劃嗎？"
                },
                {
                    "type": "text",
                    "text": "呂伯伯: 沒有特別的計劃，打算待會兒去看看園子裡的花草。聽說那邊新種了一些冬季植物。"
                },
                {
                    "type": "text",
                    "text": "2024/12/27"
                },
                {
                    "type": "text",
                    "text": "陳小姐: 是啊，馬上就要跨年了！這是一年中很特別的時刻呢。您有什麼計劃來迎接新年嗎？"
                },
                {
                    "type": "text",
                    "text": "呂伯伯: 其實我正打算參加社區的跨年活動，聽說會有煙火表演和音樂會，應該會很熱鬧。"
                },
                {
                    "type": "text",
                    "text": "陳小姐: 那聽起來很棒呢！和大家一起迎接新年，一定會很有氣氛。您還有其他準備嗎？"
                },
                {
                    "type": "text",
                    "text": "呂伯伯: 是啊，我還計劃和幾個老朋友聚一聚，大家一起吃個飯，聊聊天，回顧一下這一年發生的事情。"
                },
                {
                    "type": "text",
                    "text": "陳小姐: 這樣的聚會一定會很溫馨。和朋友們一起分享過去一年的點滴，也是很有意義的事。"
                },
                {
                    "type": "text",
                    "text": "呂伯伯: 沒錯，每次和朋友們聚會，都能讓我感受到友情的溫暖。這一年過得很快，但也很充實。"
                },
                {
                    "type": "text",
                    "text": "其他"
                },
                {
                    "type": "text",
                    "text": "2024/11/13"
                },
                {
                    "type": "text",
                    "text": "2024/11/18"
                },
                {
                    "type": "text",
                    "text": "陳小姐: 哇，真不錯！套圈圈可是需要技巧的哦。獎品是什麼呀？"
                },
                {
                    "type": "text",
                    "text": "\n"
                },
                {
                    "type": "text",
                    "text": "呂伯伯: 謝謝你，陳小姐，你也辛苦了。明天見！"
                },
                {
                    "type": "text",
                    "text": "陳小姐: 明天見，呂伯伯！祝你有個美好的夜晚。"
                },
                {
                    "type": "text",
                    "text": "2024/11/26"
                },
                {
                    "type": "text",
                    "text": "陳小姐: 好的，我也去拿一個嘗嘗。希望您今天也有個愉快的開始！"
                },
                {
                    "type": "text",
                    "text": "呂伯伯: 謝謝你，陳小姐。希望你今天也順順利利的！我們等會兒再聊。"
                },
                {
                    "type": "text",
                    "text": "陳小姐: 好的，呂伯伯，等會兒見！"
                },
                {
                    "type": "text",
                    "text": "2024/12/18"
                },
                {
                    "type": "text",
                    "text": "陳小姐: 呂伯伯，早上好！今天感覺怎麼樣？"
                },
                {
                    "type": "text",
                    "text": "呂伯伯: 早上好，陳小姐！今天感覺不錯，雖然寒流來了，天氣很冷，但我穿得暖和，還是挺舒服的。"
                },
                {
                    "type": "text",
                    "text": "陳小姐: 是啊，最近的寒流讓氣溫驟降，您一定要多注意保暖，尤其是早晚溫差大。"
                },
                {
                    "type": "text",
                    "text": "呂伯伯: 沒錯，我出門前特意多加了一件外套，還戴了圍巾。這樣走在外面也不怕冷風了。"
                },
                {
                    "type": "text",
                    "text": "\n"
                },
                {
                    "type": "text",
                    "text": "陳小姐: 哇，整理老照片一定勾起了很多回憶吧！有沒有什麼特別有趣的故事可以分享？"
                },
                {
                    "type": "text",
                    "text": "呂伯伯: 是啊，看到年輕時候的照片，想起了很多有趣的事情。有一張是我們一起去爬山，那次我們還迷了路，結果在山上過了一夜。"
                },
                {
                    "type": "text",
                    "text": "陳小姐: 哇，那一定是個難忘的經歷！不過能和朋友一起經歷這些，也是一種珍貴的回憶。"
                },
                {
                    "type": "text",
                    "text": "呂伯伯: 是的，那次經歷讓我們的友誼更深厚。現在想起來，還是覺得很有趣。"
                },
                {
                    "type": "text",
                    "text": "\n"
                },
                {
                    "type": "text",
                    "text": "呂伯伯: 好的，謝謝你，陳小姐。祝你今天也順利！"
                },
                {
                    "type": "text",
                    "text": "陳小姐: 謝謝，呂伯伯！我們下次再聊。"
                },
                {
                    "type": "text",
                    "text": "2024/12/27"
                },
                {
                    "type": "text",
                    "text": "陳小姐: 是啊，時間過得飛快。希望新的一年能帶給您更多的快樂和健康。"
                },
                {
                    "type": "text",
                    "text": "呂伯伯: 謝謝你，陳小姐。我也希望你在新的一年裡一切順利，心想事成。"
                },
                {
                    "type": "text",
                    "text": "陳小姐: 謝謝，呂伯伯！如果有什麼需要幫忙的，隨時告訴我哦。"
                },
                {
                    "type": "text",
                    "text": "呂伯伯: 好的，謝謝你，陳小姐。祝我們都有一個美好的新年！"
                },
                {
                    "type": "text",
                    "text": "陳小姐: 祝您新年快樂，我們下次再聊！"
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
                    "text": "### 身\n2024/11/13\n案主早上散步後感覺精神好多了，腰偶爾會痠，但比之前好多了。午餐時間食慾不錯，雖然有些東西咬起來不太方便，但還是吃得下。\n\n2024/11/18\n案主在套圈圈活動中站久了腰有點不舒服，後來找了個椅子坐了一會兒，感覺好多了。\n\n2024/11/26\n案主早上起得早，來食堂吃早餐，胃口不錯，選擇了粥和包子。\n\n### 心\n2024/11/13\n案主心情不錯，有時候會想念家人，但他們偶爾也會來看他。\n\n2024/11/18\n案主打算把一個小綠色盆栽放在房間裡，讓它陪著自己。今天的活動讓他很開心。\n\n2024/11/26\n案主接到老朋友的電話，聊起往事，心裡有些感慨，但聊完之後心裡暖暖的，像是重新找回了一些年輕時的熱情。\n\n2024/12/18\n案主心情不錯，開始整理一些老照片，回憶起很多美好的時光。\n\n2024/12/27\n案主心情特別好，因為快到年底了，總覺得有些期待。\n\n### 社會\n2024/11/13\n案主對週末社區的小型園遊會活動感興趣，喜歡熱鬧，可以和大家聊天。\n\n2024/11/18\n案主參加了園遊會，玩了套圈圈的遊戲，贏了一個小獎品，感到非常開心。\n\n2024/11/26\n案主和老朋友聯繫，聊起以前一起工作的時候，感到懷念和感慨時間過得真快。\n\n2024/12/18\n案主打算去看看園子裡的新種冬季植物。\n\n2024/12/27\n案主計劃參加社區的跨年活動，會有煙火表演和音樂會，並計劃和幾個老朋友聚一聚，大家一起吃飯，聊聊天，回顧這一年的事情。\n\n### 其他\n"
                }
            ]
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "呂伯伯"
                },
                {
                    "type": "text",
                    "text": "\n"
                },
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
                    "text": "陳小姐: 呂伯伯，早安啊！剛剛去散步啦？今天天氣不錯哦，適合出門走走。"
                },
                {
                    "type": "text",
                    "text": "呂伯伯: 是啊，今天天氣很好，走了一圈感覺精神好多了。"
                },
                {
                    "type": "text",
                    "text": "陳小姐: 真好！散步對身體很有幫助哦。最近腰還好嗎？有沒有不舒服的地方？"
                },
                {
                    "type": "text",
                    "text": "呂伯伯: 腰還是偶爾會痠，不過比之前好多了。"
                },
                {
                    "type": "text",
                    "text": "陳小姐: 那就好，有什麼不舒服的地方一定要告訴我們哦。午餐時間快到了，最近食慾怎麼樣？"
                },
                {
                    "type": "text",
                    "text": "呂伯伯: 食慾還不錯，雖然有些東西咬起來不太方便，但還是吃得下。"
                },
                {
                    "type": "text",
                    "text": "2024/11/18"
                },
                {
                    "type": "text",
                    "text": "呂伯伯: 其實我今天主要就是在套圈圈那裡待了很久，看到大家玩得開心，我也忍不住多試了幾次。不過，站久了我的腰有點不舒服。"
                },
                {
                    "type": "text",
                    "text": "陳小姐: 哎呀，那可要注意休息哦。要不要我幫你找個地方坐下來休息一下？"
                },
                {
                    "type": "text",
                    "text": "呂伯伯: 謝謝你，我剛剛已經找了個椅子坐了一會兒，現在感覺好多了。"
                },
                {
                    "type": "text",
                    "text": "陳小姐: 那就好，如果腰還是不舒服，記得告訴我，我們可以安排按摩或熱敷幫助舒緩。"
                },
                {
                    "type": "text",
                    "text": "\n"
                },
                {
                    "type": "text",
                    "text": "呂伯伯: 是該休息一下了，玩了一整天，現在覺得有點累。"
                },
                {
                    "type": "text",
                    "text": "陳小姐: 那就好好休息吧，有什麼需要隨時告訴我哦。希望你今晚睡個好覺！"
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
                },
                {
                    "type": "text",
                    "text": "2024/11/26"
                },
                {
                    "type": "text",
                    "text": "陳小姐: 呂伯伯，早上好！沒想到這麼早就能在食堂遇見您。"
                },
                {
                    "type": "text",
                    "text": "呂伯伯: 早啊，陳小姐！今天起得早，想來這裡吃個豐盛的早餐。"
                },
                {
                    "type": "text",
                    "text": "陳小姐: 看來您的胃口不錯呀！今天早餐有什麼特別想吃的嗎？"
                },
                {
                    "type": "text",
                    "text": "呂伯伯: 我看到有粥和包子，就拿了一些。早上吃點熱的，感覺整個人都暖和起來了。"
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
                    "text": "陳小姐: 如果有什麼需要調整的，隨時告訴我哦。我們也可以幫你看看有沒有什麼適合的食物。最近心情怎麼樣？"
                },
                {
                    "type": "text",
                    "text": "呂伯伯: 心情還不錯，有時候會想念家人，但他們偶爾也會來看我。"
                },
                {
                    "type": "text",
                    "text": "2024/11/18"
                },
                {
                    "type": "text",
                    "text": "呂伯伯: 是一個小小的綠色盆栽，我打算放在房間裡，讓它陪著我。"
                },
                {
                    "type": "text",
                    "text": "陳小姐: 這樣很好啊，有了小盆栽，房間也會多一點生氣呢。除了套圈圈，還有沒有其他有趣的事情發生？"
                },
                {
                    "type": "text",
                    "text": "\n"
                },
                {
                    "type": "text",
                    "text": "呂伯伯: 好的，我會注意的。今天的活動真的很開心，謝謝你們的精心安排。"
                },
                {
                    "type": "text",
                    "text": "陳小姐: 不客氣，只要你們開心，我們就很滿足了。那你晚上有什麼計劃嗎？要不要早點休息？"
                },
                {
                    "type": "text",
                    "text": "2024/11/26"
                },
                {
                    "type": "text",
                    "text": "陳小姐: 是啊，早上的粥最能暖胃了。對了，呂伯伯，您最近心情怎麼樣？"
                },
                {
                    "type": "text",
                    "text": "呂伯伯: 最近心情還不錯，只是昨天接到一個老朋友的電話，聊起了一些往事，心裡有些感慨。"
                },
                {
                    "type": "text",
                    "text": "\n"
                },
                {
                    "type": "text",
                    "text": "呂伯伯: 沒錯，聊完之後，我也覺得心裡暖暖的，像是重新找回了一些年輕時的熱情。"
                },
                {
                    "type": "text",
                    "text": "陳小姐: 那真是太好了。保持這種心情，對身體和生活都有很大的幫助呢。"
                },
                {
                    "type": "text",
                    "text": "呂伯伯: 是啊，心情好，吃飯也香。今天的包子特別好吃，你也試試吧。"
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
                    "text": "陳小姐: 那聽起來很不錯呢，冬季的植物也別有一番風味。對了，最近心情怎麼樣？"
                },
                {
                    "type": "text",
                    "text": "呂伯伯: 最近心情不錯，上次和老朋友聊完之後，我也開始整理一些老照片，回憶起很多美好的時光。"
                },
                {
                    "type": "text",
                    "text": "\n"
                },
                {
                    "type": "text",
                    "text": "陳小姐: 聽您這麼說，我都能感受到那種冒險的樂趣了。保持這種愉快的心情，生活也會更加美好。"
                },
                {
                    "type": "text",
                    "text": "呂伯伯: 謝謝你，陳小姐。和你聊聊天，我也覺得心情更好了。"
                },
                {
                    "type": "text",
                    "text": "陳小姐: 不客氣，呂伯伯。希望您今天有個愉快的一天！如果有什麼需要，隨時告訴我哦。"
                },
                {
                    "type": "text",
                    "text": "2024/12/27"
                },
                {
                    "type": "text",
                    "text": "陳小姐: 呂伯伯，早上好！今天感覺怎麼樣？"
                },
                {
                    "type": "text",
                    "text": "呂伯伯: 早上好，陳小姐！今天心情特別好，因為快到年底了，總覺得有些期待。"
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
                    "text": "陳小姐: 家人來看你一定很開心吧！這週末社區有個小活動，你有興趣參加嗎？"
                },
                {
                    "type": "text",
                    "text": "呂伯伯: 蛤，是甚麼活動啊?"
                },
                {
                    "type": "text",
                    "text": "陳小姐: 這週末我們會舉辦一個小型的園遊會活動，地點就在中心的花園裡。到時候會有一些攤位遊戲、音樂表演，還有手工藝品展示。大家可以一起來參加，享受一下熱鬧的氣氛，也可以試試看不同的小吃哦。"
                },
                {
                    "type": "text",
                    "text": "\n"
                },
                {
                    "type": "text",
                    "text": "呂伯伯: 聽起來很有趣呢！我最喜歡熱鬧了，我也可以和大家聊天。"
                },
                {
                    "type": "text",
                    "text": "\n"
                },
                {
                    "type": "text",
                    "text": "陳小姐: 是啊，這樣的活動也是一個認識新朋友的好機會。如果你有什麼想試試看的遊戲或活動，可以告訴我，我幫你安排。"
                },
                {
                    "type": "text",
                    "text": "2024/11/18"
                },
                {
                    "type": "text",
                    "text": "陳小姐: 呂伯伯，下午好！今天的園遊會玩得怎麼樣啊？"
                },
                {
                    "type": "text",
                    "text": "呂伯伯: 哎呀，陳小姐，今天真是太開心了！我參加了一個套圈圈的遊戲，居然還贏了一個小獎品呢！"
                },
                {
                    "type": "text",
                    "text": "2024/11/26"
                },
                {
                    "type": "text",
                    "text": "陳小姐: 原來如此，老朋友的聯繫總是讓人感觸良多。是什麼樣的往事呢？"
                },
                {
                    "type": "text",
                    "text": "呂伯伯: 我們聊到了以前一起工作的時候，想起那時候一起努力的日子，真是懷念啊。也有點感慨時間過得真快。"
                },
                {
                    "type": "text",
                    "text": "陳小姐: 是啊，回憶總是美好的。能夠和老朋友敘舊，也是很珍貴的事情呢。"
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
                    "text": "陳小姐: 做得對！有時候天氣變化太快，身體容易不適應。今天有什麼特別的計劃嗎？"
                },
                {
                    "type": "text",
                    "text": "呂伯伯: 沒有特別的計劃，打算待會兒去看看園子裡的花草。聽說那邊新種了一些冬季植物。"
                },
                {
                    "type": "text",
                    "text": "2024/12/27"
                },
                {
                    "type": "text",
                    "text": "陳小姐: 是啊，馬上就要跨年了！這是一年中很特別的時刻呢。您有什麼計劃來迎接新年嗎？"
                },
                {
                    "type": "text",
                    "text": "呂伯伯: 其實我正打算參加社區的跨年活動，聽說會有煙火表演和音樂會，應該會很熱鬧。"
                },
                {
                    "type": "text",
                    "text": "陳小姐: 那聽起來很棒呢！和大家一起迎接新年，一定會很有氣氛。您還有其他準備嗎？"
                },
                {
                    "type": "text",
                    "text": "呂伯伯: 是啊，我還計劃和幾個老朋友聚一聚，大家一起吃個飯，聊聊天，回顧一下這一年發生的事情。"
                },
                {
                    "type": "text",
                    "text": "陳小姐: 這樣的聚會一定會很溫馨。和朋友們一起分享過去一年的點滴，也是很有意義的事。"
                },
                {
                    "type": "text",
                    "text": "呂伯伯: 沒錯，每次和朋友們聚會，都能讓我感受到友情的溫暖。這一年過得很快，但也很充實。"
                },
                {
                    "type": "text",
                    "text": "其他"
                },
                {
                    "type": "text",
                    "text": "2024/11/13"
                },
                {
                    "type": "text",
                    "text": "2024/11/18"
                },
                {
                    "type": "text",
                    "text": "陳小姐: 哇，真不錯！套圈圈可是需要技巧的哦。獎品是什麼呀？"
                },
                {
                    "type": "text",
                    "text": "\n"
                },
                {
                    "type": "text",
                    "text": "呂伯伯: 謝謝你，陳小姐，你也辛苦了。明天見！"
                },
                {
                    "type": "text",
                    "text": "陳小姐: 明天見，呂伯伯！祝你有個美好的夜晚。"
                },
                {
                    "type": "text",
                    "text": "2024/11/26"
                },
                {
                    "type": "text",
                    "text": "陳小姐: 好的，我也去拿一個嘗嘗。希望您今天也有個愉快的開始！"
                },
                {
                    "type": "text",
                    "text": "呂伯伯: 謝謝你，陳小姐。希望你今天也順順利利的！我們等會兒再聊。"
                },
                {
                    "type": "text",
                    "text": "陳小姐: 好的，呂伯伯，等會兒見！"
                },
                {
                    "type": "text",
                    "text": "2024/12/18"
                },
                {
                    "type": "text",
                    "text": "陳小姐: 呂伯伯，早上好！今天感覺怎麼樣？"
                },
                {
                    "type": "text",
                    "text": "呂伯伯: 早上好，陳小姐！今天感覺不錯，雖然寒流來了，天氣很冷，但我穿得暖和，還是挺舒服的。"
                },
                {
                    "type": "text",
                    "text": "陳小姐: 是啊，最近的寒流讓氣溫驟降，您一定要多注意保暖，尤其是早晚溫差大。"
                },
                {
                    "type": "text",
                    "text": "呂伯伯: 沒錯，我出門前特意多加了一件外套，還戴了圍巾。這樣走在外面也不怕冷風了。"
                },
                {
                    "type": "text",
                    "text": "\n"
                },
                {
                    "type": "text",
                    "text": "陳小姐: 哇，整理老照片一定勾起了很多回憶吧！有沒有什麼特別有趣的故事可以分享？"
                },
                {
                    "type": "text",
                    "text": "呂伯伯: 是啊，看到年輕時候的照片，想起了很多有趣的事情。有一張是我們一起去爬山，那次我們還迷了路，結果在山上過了一夜。"
                },
                {
                    "type": "text",
                    "text": "陳小姐: 哇，那一定是個難忘的經歷！不過能和朋友一起經歷這些，也是一種珍貴的回憶。"
                },
                {
                    "type": "text",
                    "text": "呂伯伯: 是的，那次經歷讓我們的友誼更深厚。現在想起來，還是覺得很有趣。"
                },
                {
                    "type": "text",
                    "text": "\n"
                },
                {
                    "type": "text",
                    "text": "呂伯伯: 好的，謝謝你，陳小姐。祝你今天也順利！"
                },
                {
                    "type": "text",
                    "text": "陳小姐: 謝謝，呂伯伯！我們下次再聊。"
                },
                {
                    "type": "text",
                    "text": "2024/12/27"
                },
                {
                    "type": "text",
                    "text": "陳小姐: 是啊，時間過得飛快。希望新的一年能帶給您更多的快樂和健康。"
                },
                {
                    "type": "text",
                    "text": "呂伯伯: 謝謝你，陳小姐。我也希望你在新的一年裡一切順利，心想事成。"
                },
                {
                    "type": "text",
                    "text": "陳小姐: 謝謝，呂伯伯！如果有什麼需要幫忙的，隨時告訴我哦。"
                },
                {
                    "type": "text",
                    "text": "呂伯伯: 好的，謝謝你，陳小姐。祝我們都有一個美好的新年！"
                },
                {
                    "type": "text",
                    "text": "陳小姐: 祝您新年快樂，我們下次再聊！"
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
                    "text": "### 身\n2024/11/13\n案主早上散步後感覺精神好多了，腰偶爾會痠，但比之前好多了。午餐時間食慾不錯，雖然有些東西咬起來不太方便，但還是吃得下。\n\n2024/11/18\n案主在套圈圈活動中站久了腰有點不舒服，後來找了個椅子坐了一會兒，感覺好多了。\n\n2024/11/26\n案主早上起得早，來食堂吃早餐，胃口不錯，選擇了粥和包子。\n\n### 心\n2024/11/13\n案主心情不錯，有時候會想念家人，但他們偶爾也會來看他。\n\n2024/11/18\n案主打算把一個小綠色盆栽放在房間裡，讓它陪著自己。今天的活動讓他很開心。\n\n2024/11/26\n案主接到老朋友的電話，聊起往事，心裡有些感慨，但聊完之後心裡暖暖的，像是重新找回了一些年輕時的熱情。\n\n2024/12/18\n案主心情不錯，開始整理一些老照片，回憶起很多美好的時光。\n\n2024/12/27\n案主心情特別好，因為快到年底了，總覺得有些期待。\n\n### 社會\n2024/11/13\n案主對週末社區的小型園遊會活動感興趣，喜歡熱鬧，可以和大家聊天。\n\n2024/11/18\n案主參加了園遊會，玩了套圈圈的遊戲，贏了一個小獎品，感到非常開心。\n\n2024/11/26\n案主和老朋友聯繫，聊起以前一起工作的時候，感到懷念和感慨時間過得真快。\n\n2024/12/18\n案主打算去看看園子裡的新種冬季植物。\n\n2024/12/27\n案主計劃參加社區的跨年活動，會有煙火表演和音樂會，並計劃和幾個老朋友聚一聚，大家一起吃飯，聊聊天，回顧這一年的事情。\n\n### 其他\n"
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