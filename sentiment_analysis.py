# sentiment_analysis.py

from redis_utils import get_recent_messages
from azure_openai import chat35
from langchain.schema import HumanMessage
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

prompt = ChatPromptTemplate.from_messages([
    ("system", "使用繁體中文分析對方情緒，解釋情緒原因，並給出兩個回復建議。\n"
                "回覆風格:{style}\n"
               "{format_instructions}"),
    ("human", "{query}")
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

def analyze_sentiment(group_id, my_user_id, reply_style, limit=50):
    recent_messages = get_recent_messages(group_id, limit=limit)
    
    if not recent_messages:
        return {
            "name": "Unknown",
            "mbti": "Unknown",
            "emotion": "Unknown",
            "suggestions": ["No recent messages", "Unable to analyze"]
        }
    
    name, mbti= get_opponent_user_info(group_id, my_user_id)

    all_messages = "\n".join([msg['content'] for msg in recent_messages])
    query = f'請分析以下{len(recent_messages)}，並根據"{reply_style}"的風格給出回覆建議：\n{all_messages}'
    user_prompt = new_prompt.invoke({"query": query, "style":reply_style})

    try:
        response = chat35.invoke(user_prompt)
        analysis = parser.parse(response.content)
        return {
            "name": name,
            "mbti": mbti,
            "emotion": analysis.emotion,
            "suggestions": analysis.reply_suggestions
        }
    except Exception as e:
        print(f"Error during analysis: {str(e)}")
        return {
            "name": name,
            "mbti": mbti,
            "emotion": "Error",
            "suggestions": ["分析時出錯", str(e)]
        }
