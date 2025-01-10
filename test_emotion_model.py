import threading
from transformers import BertTokenizer, BertForSequenceClassification
import torch

def run_model_with_timeout(model, inputs, timeout=10):
    result = {}
    def target():
        try:
            outputs = model(**inputs)
            print(outputs)
            result['outputs'] = outputs
        except Exception as e:
            result['error'] = str(e)

    thread = threading.Thread(target=target)
    thread.start()
    thread.join(timeout)  # 設置超時時間

    if thread.is_alive():
        raise TimeoutError("模型推理超時")
    if 'error' in result:
        raise RuntimeError(result['error'])
    return result['outputs']

# 主程式
model_path = "emotion_models/happiness"
try:
    tokenizer = BertTokenizer.from_pretrained(model_path)
    model = BertForSequenceClassification.from_pretrained(model_path)
    print("模型加載成功")

    # 準備輸入
    text = "這是一個測試文本"
    inputs = tokenizer(text, return_tensors="pt", padding="max_length", truncation=True, max_length=128)
    print("輸入已準備:", inputs)

    # 使用超時機制運行模型
    outputs = run_model_with_timeout(model, inputs, timeout=10)
    print("模型輸出:", outputs)

    probabilities = torch.softmax(outputs.logits, dim=1)
    print("模型概率分佈:", probabilities)
except TimeoutError as te:
    print("超時錯誤:", te)
except RuntimeError as re:
    print("運行時錯誤:", re)
except Exception as e:
    print(f"加載或執行模型時出現錯誤: {e}")
