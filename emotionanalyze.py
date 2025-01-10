'''
app
azure_openai.py
'''
'''
from langchain.llms import AzureOpenAI
from langchain.chat_models import AzureChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.schema import HumanMessage
'''
import json
import logging
import re
from langchain_community.chat_models import AzureChatOpenAI
from langchain.schema import HumanMessage
from enum import Enum

logging.basicConfig(level=logging.INFO)

class Emotion(Enum):
    HAPPY = "幸福"
    JOYFUL = "喜悅"
    SATISFIED = "滿足"
    EXCITED = "興奮"
    GRIEVED = "悲痛"
    DISAPPOINTED = "失望"
    DEPRESSED = "沮喪"
    MELANCHOLIC = "憂鬱"
    ANGRY = "生氣"
    FURIOUS = "憤怒"
    ENRAGED = "激怒"
    INDIGNANT = "憤慨"
    SCARED = "害怕"
    FEARFUL = "恐懼"
    PANICKED = "驚慌"
    ANXIOUS = "焦慮"
    DISGUSTED = "反感"
    REPULSED = "厭惡"
    REJECTED = "排斥"
    DISLIKED = "嫌惡"
    SURPRISED = "驚訝"
    SHOCKED = "震驚"
    ASTONISHED = "驚奇"
    STUNNED = "錯愕"
    OTHER = "其他"

class MBTIDialogueAnalyzer:
    def __init__(self, name1, mbti1, name2, mbti2):
        self.people = {
            name1: {'mbti': mbti1},
            name2: {'mbti': mbti2}
        }
        self.chat_model = AzureChatOpenAI(
            deployment_name='ETHCI',
            openai_api_version='2023-05-15',
            openai_api_key='e67e05c67d424ef1b7ffbbc14e589b32',
            openai_api_base='https://lingpu.im.tku.edu.tw',
            openai_api_type='azure',
            model='gpt-35-turbo',
            temperature=0.7,
            max_tokens=1000
        )

    def analyze_emoji(self, text):
        emoji_pattern = re.compile("["
            u"\U0001F600-\U0001F64F"  # emoticons
            u"\U0001F300-\U0001F5FF"  # symbols & pictographs
            u"\U0001F680-\U0001F6FF"  # transport & map symbols
            u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
            u"\U00002702-\U000027B0"
            u"\U000024C2-\U0001F251"
            "]+", flags=re.UNICODE)

        emojis = emoji_pattern.findall(text)

        if not emojis:
            return {}

        prompt = f"""
        請分析以下表情符號的情緒：
        {' '.join(emojis)}

        請用以下JSON格式回應，為每個表情符號選擇一個最貼切的情緒：
        {{
            "emoji1": "情緒1",
            "emoji2": "情緒2",
            ...
        }}
        """

        try:
            response = self.chat_model([HumanMessage(content=prompt)])
            return json.loads(response.content)
        except Exception as e:
            logging.error(f"Error in analyze_emoji: {str(e)}")
            return {}

    def analyze_dialogue(self, msg, analyzer_name):
        other_name = next(name for name in self.people.keys() if name != analyzer_name)

        emoji_analysis = self.analyze_emoji(msg)
        emoji_info = ", ".join([f"{emoji}: {emotion}" for emoji, emotion in emoji_analysis.items()])

        emotions_list = ", ".join([e.value for e in Emotion if e != Emotion.OTHER])
        prompt = f"""
        基於MBTI人格特質，{analyzer_name}是{self.people[analyzer_name]['mbti']}，{other_name}是{self.people[other_name]['mbti']}

        對話內容：
        {msg}

        表情符號分析結果（如果有的話，僅供參考）：
        {emoji_info}

        請仔細分析對話內容，包括文字和表情符號（如果有的話）。根據整體語境和表達方式，從以下情緒中選擇最符合{other_name}的情緒：
        {emotions_list}
        請注意，即使沒有表情符號，也要根據文字內容判斷情緒。只有在真的無法判斷時，才標記為"其他"。請務必只從上述列表中選擇情緒，不要使用列表外的情緒詞彙。

        分析兩個人的對話內容，請概括{other_name}想表達的核心要點是什麼？

        請用如下json格式回應:
        {{
            "{other_name}_emotion": "",
            "key_point": ""
        }}
        """

        try:
            response = self.chat_model([HumanMessage(content=prompt)])
            analysis = json.loads(response.content)
            logging.info(f"AI response: {analysis}")

            # 確保返回的情緒在 Emotion 枚舉中
            emotion = analysis[f"{other_name}_emotion"]
            if emotion not in [e.value for e in Emotion]:
                emotion = Emotion.OTHER.value

            return {
                f"{other_name}的情緒": emotion,
                "對方想表達的重點": analysis["key_point"]
            }
        except Exception as e:
            logging.error(f"Error in analyze_dialogue: {str(e)}")
            return {}

    def get_response(self, msg, style, initial_analysis, analyzer_name):
        other_name = next(name for name in self.people.keys() if name != analyzer_name)

        prompt = f"""
        基於MBTI人格特質，{analyzer_name}是{self.people[analyzer_name]['mbti']}

        {msg}

        {other_name}的情緒: {initial_analysis[f'{other_name}的情緒']}
        {other_name}想表達的重點: {initial_analysis['對方想表達的重點']}

        請用以下風格為{analyzer_name}生成兩句建議回應: {style}

        請用如下json格式回應:
        {{
            "response1": "",
            "response2": ""
        }}
        """

        try:
            response = self.chat_model([HumanMessage(content=prompt)])
            return json.loads(response.content)
        except Exception as e:
            logging.error(f"Error in get_response: {str(e)}")
            return {}

def get_style_choice():
    styles = ["正式", "輕鬆", "幽默", "同情", "熱情", "客觀"]
    print("請選擇回應風格：")
    for i, style in enumerate(styles, 1):
        print(f"{i}. {style}")

    while True:
        try:
            choice = int(input("請輸入您的選擇（1-6）："))
            if 1 <= choice <= 6:
                return styles[choice - 1]
            else:
                print("無效的選擇，請輸入1到6之間的數字。")
        except ValueError:
            print("請輸入有效的數字。")

def main():
    print("歡迎使用MBTI對話分析系統！")

    name1 = input("請輸入第一個人的名字（將替換對話中的A）：")
    mbti1 = input(f"請輸入{name1}的MBTI類型：")
    name2 = input("請輸入第二個人的名字（將替換對話中的B）：")
    mbti2 = input(f"請輸入{name2}的MBTI類型：")

    analyzer = MBTIDialogueAnalyzer(name1, mbti1, name2, mbti2)

    msg = f'{name1}：你事情做完了沒😡 {name2}：還沒ㄟ怎麼了 {name1}：還要我等多久 {name2}：對不起再給我幾分鐘'

    analyzer_choice = input(f"請選擇分析者（{name1} 或 {name2}）：")
    while analyzer_choice not in [name1, name2]:
        analyzer_choice = input(f"無效的選擇，請輸入 {name1} 或 {name2}：")

    other_party = name2 if analyzer_choice == name1 else name1

    print("\n正在分析對話，請稍候...")
    initial_analysis = analyzer.analyze_dialogue(msg, analyzer_choice)

    if not initial_analysis:
        print("分析過程中出現錯誤，請檢查日誌並重試。")
        return

    print(f'\n{name1}的人格: {analyzer.people[name1]["mbti"]}')
    print(f'{name2}的人格: {analyzer.people[name2]["mbti"]}')
    print(f'{other_party}的情緒：{initial_analysis[f"{other_party}的情緒"]}')
    print(f'{other_party}想表達的重點：{initial_analysis["對方想表達的重點"]}')

    style = get_style_choice()

    print("\n正在生成回應，請稍候...")
    response = analyzer.get_response(msg, style, initial_analysis, analyzer_choice)

    if not response:
        print("生成回應時出現錯誤，請檢查日誌並重試。")
        return

    final_result = {
        f"{name1}的人格": analyzer.people[name1]["mbti"],
        f"{name2}的人格": analyzer.people[name2]["mbti"],
        f"{other_party}的情緒": initial_analysis[f"{other_party}的情緒"],
        f"{other_party}想表達的重點": initial_analysis["對方想表達的重點"],
        "建議回應1": response.get("response1", ""),
        "建議回應2": response.get("response2", "")
    }

    print("\n生成的回應：")
    print(json.dumps(final_result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()


#res = llm35(prompt=msg)
#print(f'\nllm35: {res}')

#res = chat35([HumanMessage(content=msg)])
#print(f'\nchat35: {res.content}')

#res = chat4([HumanMessage(content=msg)])
#print(f'\nchat4: {res.content}')

#e = embeddings.embed_query(msg)
#print(f'\nembed: len(e)={len(e)}')

# 臉部表情符號
smile = "😁"  # 大笑
joy = "😂"  # 喜極而泣
blush = "😊"  # 害羞
heart_eyes = "😍"  # 愛心眼
kissing_heart = "😘"  # 親吻
hugging = "🤗"  # 擁抱
thinking = "🤔"  # 思考
sleeping = "😴"  # 睡覺
winking = "😜"  # 眨眼
rage = "😡"  # 生氣
cry = "😢"  # 哭泣
scream = "😱"  # 驚恐
drooling = "🤤"  # 流口水
mask = "😷"  # 戴口罩

# 手勢表情符號
thumbs_up = "👍"  # 豎起大拇指
thumbs_down = "👎"  # 大拇指向下
clap = "👏"  # 鼓掌
victory = "✌️"  # 勝利手勢
crossed_fingers = "🤞"  # 交叉手指
fist_bump = "👊"  # 拳擊
handshake = "🤝"  # 握手
raised_hands = "🙌"  # 舉起雙手
open_hands = "👐"  # 張開的手
ok_hand = "👌"  # OK 手勢

# 物體和符號
tada = "🎉"  # 驚喜
light_bulb = "💡"  # 電燈泡
books = "📚"  # 書本
art = "🎨"  # 藝術
musical_note = "🎵"  # 音符
soccer = "⚽"  # 足球
apple = "🍎"  # 蘋果
car = "🚗"  # 汽車
airplane = "✈️"  # 飛機
computer = "💻"  # 電腦

# 心形表情符號
heart = "❤️"  # 心
broken_heart = "💔"  # 破碎的心
two_hearts = "💕"  # 兩顆心
sparkling_heart = "💖"  # 閃亮的心
growing_heart = "💗"  # 成長的心
heart_with_arrow = "💘"  # 帶箭頭的心
heart_with_ribbon = "💝"  # 帶絲帶的心

# 天氣表情符號
sun = "☀️"  # 太陽
cloud_rain = "🌧️"  # 雨雲
cloud_lightning = "🌩️"  # 雷雲
cloud_snow = "🌨️"  # 雪雲
rainbow = "🌈"  # 彩虹
snowflake = "❄️"  # 雪花