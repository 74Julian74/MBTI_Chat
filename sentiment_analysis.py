# sentiment_analysis.py

from redis_utils import get_recent_messages
#from azure_openai import chat35, chat4
from langchain.schema import HumanMessage, SystemMessage, AIMessage
from typing import List
from langchain.output_parsers import PydanticOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from dbmodels import db, UserACC, UserMSG
from openai_client import get_chat_completion
import logging
from flask import current_app

logger = logging.getLogger(__name__)


class ChatAnalysis(BaseModel):
    emotion: str = Field(description="對方的情緒分析，如開心、沮喪、生氣等")
    emotion_reason: str = Field(description="情緒分析的理由")
    reply_suggestions: List[str] = Field(description="兩個直接可用的回覆建議", min_items=2, max_items=2)

parser = PydanticOutputParser(pydantic_object=ChatAnalysis)
format_instructions = parser.get_format_instructions()
print("格式為:", format_instructions)

prompt = ChatPromptTemplate.from_messages([
    ("system", "您現在是 {analyzer_name} (MBTI: {analyzer_mbti})，正在與 {target_name} (MBTI: {target_mbti}) 對話。"
                "請以 {analyzer_name} 的身份直接回覆 {target_name}。\n"
                "請使用繁體中文僅分析 {target_name} 的情緒，解釋情緒原因，並給出兩個回復建議。"
                "這些建議應該是完整的句子，可以直接發送給 {target_name}。"
                "請忽略自己（{analyzer_name}）的消息內容，只關注 {target_name} 的消息。\n"
                "回覆風格: {style}\n"
                "請務必按照以下格式回答：\n"
                "{format_instructions}"),
    ("human", "以下是完整對話記錄，請特別關注並分析 {target_name} 的消息：\n\n{query}\n\n"
              "請分析 {target_name} 的情緒，解釋原因，並提供兩個直接可用的回復建議。"),
    ("ai", "根據 {target_name} 的消息，我的分析如下：")
])
new_prompt = prompt.partial(format_instructions=format_instructions)


def get_user_info(user_id):
    user = UserACC.query.get(user_id)
    if user:
        return user.username, user.MBTI
    return "Unknown", "Unknown"

def get_opponent_user_info(group_id, my_user_id):
    try:
        opponent = UserMSG.query.filter(
            UserMSG.GroupID == group_id, 
            UserMSG.SenderID != my_user_id
        ).order_by(UserMSG.TimeStamp.desc()).first()

        if opponent:
            opponent_user = UserACC.query.get(opponent.SenderID)
            if opponent_user:
                return {
                    'id': opponent_user.UserID,
                    'name': opponent_user.username,
                    'mbti': opponent_user.MBTI
                }
    except Exception as e:
        logger.error(f"Error in get_opponent_user_info: {str(e)}", exc_info=True)
    
    return None

mbti_explanations = {
    'E': '外向型 (Extraversion): 從外部世界獲取能量，喜歡社交互動',
    'I': '內向型 (Introversion): 從內心世界獲取能量，喜歡獨處思考',
    'S': '感覺型 (Sensing): 注重具體事實和細節，依賴實際經驗',
    'N': '直覺型 (Intuition): 注重概念和可能性，喜歡想像和創新',
    'T': '思考型 (Thinking): 邏輯決策，注重客觀分析',
    'F': '情感型 (Feeling): 價值觀決策，注重人際和諧',
    'J': '判斷型 (Judging): 喜歡計劃和組織，追求確定性',
    'P': '知覺型 (Perceiving): 靈活適應，喜歡保持選擇開放'
}

def get_mbti_explanation(mbti_type):
    """
    根據給定的 MBTI 類型返回每個維度的解釋
    """
    if not mbti_type or len(mbti_type) != 4:
        return "無效的 MBTI 類型"
    
    explanation = "MBTI 類型解釋：\n"
    for letter in mbti_type:
        if letter in mbti_explanations:
            explanation += f"{mbti_explanations[letter]}\n"
        else:
            explanation += f"未知字母：{letter}\n"
    
    return explanation.strip()

def analyze_sentiment(group_id, my_user_id, opponent_info, reply_style, limit=20):
    if not group_id or not opponent_info:
        return {
            "name": "Unknown",
            "mbti": "Unknown",
            "emotion": "Unknown",
            "suggestions": ["No active chat room", "Unable to analyze"]
        }

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
    target_name, target_mbti = opponent_info['name'], opponent_info['mbti']
    mbti_explanation = get_mbti_explanation(target_mbti)
    
    opponent_messages = []
    context_messages = []

    for msg in recent_messages:
        sender_id = msg.get('SenderID') or msg.get('sender_id')
        content = msg.get('content', 'No content')
        
        if str(sender_id) == str(opponent_info['id']):
            opponent_messages.append(f"[對方:{target_name}] {content}")
        else:
            context_messages.append(f"[其他人] {content}")

    opponent_messages_str = "\n".join(opponent_messages)
    context_messages_str = "\n".join(context_messages)    

    query = (f"請僅分析以下來自 {target_name} 的消息：\n\n{opponent_messages_str}\n\n"
             f"上下文信息（僅供參考，不需要分析）：\n{context_messages_str}\n\n"
             f"{target_name} 的 MBTI 類型是 {target_mbti}。以下是解釋：\n{mbti_explanation}\n\n"
             f"作為 {analyzer_name}，請專注分析 {target_name} 的情緒並提供回復建議。"
             f"在分析時，請考慮 {target_name} 的 MBTI 類型特徵。"
             f"嚴格忽略其他人的消息，只關注 {target_name} 的表達。")
    
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
    # 使用 OpenAI API 進行分析
    messages = [
        {"role": "system", "content": user_prompt.messages[0].content},
        {"role": "user", "content": user_prompt.messages[1].content},
        {"role": "assistant", "content": user_prompt.messages[2].content}
    ]
    
    response_content = get_chat_completion(messages)

    if response_content:
        print("原始回答為:", response_content)
        # 嘗試提取 JSON
        json_start = response_content.find('{')
        json_end = response_content.rfind('}') + 1
        if json_start != -1 and json_end != -1:
            json_content = response_content[json_start:json_end]
            analysis = parser.parse(json_content)
        else:
            raise ValueError("无法找到有效的JSON内容")

        return {
            "name": target_name,
            "mbti": target_mbti,
            "mbti_explanation": mbti_explanation,
            "emotion": analysis.emotion,
            "emotion_reason": analysis.emotion_reason,
            "suggestions": analysis.reply_suggestions
        }
    else:
        return {
            "name": target_name,
            "mbti": target_mbti,
            "emotion": "Error",
            "suggestions": ["分析時出錯", "無法取得OpenAI回應"]
        }

'''
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
'''
    
