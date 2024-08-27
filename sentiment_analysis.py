# sentiment_analysis.py

from redis_utils import get_recent_messages
from azure_openai import chat35
from langchain.schema import HumanMessage

def analyze_sentiment(room_id, limit= 50):
    # 獲取最近的一條消息
    recent_messages = get_recent_messages(room_id, limit= limit)
    
    if not recent_messages:
        return "No recent messages found in the specified room."

    # 將所有消息合併成一個字符串
    all_messages = "\n".join([msg['content'] for msg in recent_messages])

    # 將消息插入到預定義的提示中
    msg = f'請分析以下{len(recent_messages)}條消息的整體情緒：\n{all_messages}'

    # 使用 Azure OpenAI 進行情緒分析
    response = chat35([HumanMessage(content=msg)])

    # 返回分析結果
    return response.content

# 使用示例
if __name__ == "__main__":
    room_id = "default_room"  # 替換為實際的房間 ID
    result = analyze_sentiment(room_id)
    
    print(f"情緒分析結果: {result}")