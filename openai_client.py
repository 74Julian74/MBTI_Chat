import openai

openai.api_key='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'

def get_chat_completion(messages, max_tokens=1000, temperature=0.8):
    try:
        # 呼叫 OpenAI ChatCompletion API
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )
        # 回傳 AI 回應
        return response['choices'][0]['message']['content']
    except Exception as e:
        print(f"Error during API call: {str(e)}")
        return None