# sentiment_analysis.py

from redis_utils import get_recent_messages
from azure_openai import chat35, chat4
from langchain.schema import HumanMessage, SystemMessage, AIMessage
from typing import List
from langchain.output_parsers import PydanticOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from dbmodels import db, UserACC, UserMSG

class ChatAnalysis(BaseModel):
    emotion: str = Field(description="對方的情緒分析，如開心、沮喪、生氣等")
    emotion_reason: str = Field(description="情緒分析的理由")
    reply_suggestions: List[str] = Field(description="兩個回覆建議", min_items=2, max_items=2)

parser = PydanticOutputParser(pydantic_object=ChatAnalysis)
format_instructions = parser.get_format_instructions()
print("格式為:", format_instructions)

prompt = ChatPromptTemplate.from_messages([
    ("system", "您現在是 {analyzer_name} (MBTI: {analyzer_mbti})，正在與 {target_name} (MBTI: {target_mbti}) 對話。"
                "請以 {analyzer_name} 的身份直接回覆 {target_name}。\n"
                "請使用繁體中文分析 {target_name} 的情緒，解釋情緒原因，並給出兩個回復建議。\n"
                "回覆風格: {style}\n"
                "請務必按照以下格式回答：\n"
                "{format_instructions}"),
    ("human", "{query}"),
    ("ai", "根據對話，我的回覆是：")
])
new_prompt = prompt.partial(format_instructions=format_instructions)


def get_user_info(user_id):
    user = UserACC.query.get(user_id)
    if user:
        return user.username, user.MBTI
    return "Unknown", "Unknown"

def get_opponent_user_info(group_id, my_user_id):
    opponent= UserMSG.query.filter(UserMSG.GroupID== group_id, UserMSG.SenderID!= my_user_id).first() 

    if opponent:
        opponent_user_id= opponent.SenderID
        name, mbti= get_user_info(opponent_user_id)
        return name, mbti
    return "Unknown", "Unknown"

def analyze_sentiment(group_id, my_user_id, reply_style, limit=20):
    # 获取最近的消息，限制为20条
    all_messages = get_recent_messages(group_id)
    recent_messages = all_messages[-limit:]  # 只取最后20条消息
    
    if not recent_messages:
        return {
            "name": "Unknown",
            "mbti": "Unknown",
            "emotion": "Unknown",
            "suggestions": ["No recent messages", "Unable to analyze"]
        }
    
    analyzer_name, analyzer_mbti = get_user_info(my_user_id)
    target_name, target_mbti = get_opponent_user_info(group_id, my_user_id)

    formatted_messages = []
    for msg in recent_messages:
        sender_name, _ = get_user_info(msg['sender_id'])
        role = "對方" if sender_name == target_name else "您"
        formatted_messages.append(f"[{role}:{sender_name}] {msg['content']}")

    all_messages = "\n".join(formatted_messages)
    query = f'請分析以下{len(recent_messages)}句對話，重點關注最近的消息：\n{all_messages}\n'
    query += f"作為 {analyzer_name}，請分析 {target_name} 的情緒並提供回復建議。"
    
    user_prompt = new_prompt.invoke({
        "query": query,
        "style": reply_style,
        "analyzer_name": analyzer_name,
        "analyzer_mbti": analyzer_mbti,
        "target_name": target_name,
        "target_mbti": target_mbti
    })
    #設定不要超過進入OPENAI長度
    #讓openai了解是誰傳送的訊息，讓他知道是誰要回答
    try:
        response = chat35.invoke([
            SystemMessage(content=user_prompt.messages[0].content),
            HumanMessage(content=user_prompt.messages[1].content),
            AIMessage(content=user_prompt.messages[2].content)
        ])
        print("原始回答為:", response.content)
        
        # 尝试提取JSON部分
        json_start = response.content.find('{')
        json_end = response.content.rfind('}') + 1
        if json_start != -1 and json_end != -1:
            json_content = response.content[json_start:json_end]
            analysis = parser.parse(json_content)
        else:
            raise ValueError("无法找到有效的JSON内容")

        return {
            "name": target_name,
            "mbti": target_mbti,
            "emotion": analysis.emotion,
            "emotion_reason": analysis.emotion_reason,
            "suggestions": analysis.reply_suggestions
        }
    except Exception as e:
        print(f"Error during analysis: {str(e)}")
        return {
            "name": target_name,
            "mbti": target_mbti,
            "emotion": "Error",
            "suggestions": ["分析時出錯", str(e)]
        }
