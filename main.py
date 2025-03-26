import torch
from datetime import datetime
from torch.utils.data import Dataset, DataLoader
from transformers import BertTokenizer, BertForSequenceClassification
from transformers import AdamW
import pandas as pd
from sklearn.model_selection import train_test_split
from redis_utils import get_recent_messages
from flask import current_app
from concurrent.futures import ThreadPoolExecutor, TimeoutError
import numpy as np
from functools import lru_cache
from datetime import datetime, timedelta
import os
import json
import time
import traceback

class EmotionDataset(Dataset):
    def __init__(self, texts, labels, tokenizer, max_len=128):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_len = max_len

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        text = str(self.texts[idx])
        label = self.labels[idx]

        encoding = self.tokenizer.encode_plus(
            text,
            add_special_tokens=True,
            max_length=self.max_len,
            padding='max_length',
            truncation=True,
            return_attention_mask=True,
            return_tensors='pt'
        )

        return {
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
            'labels': torch.tensor(label, dtype=torch.long)
        }

class EmotionPredictor:
    def __init__(self, models_base_path='emotion_models'):
        print(f"初始化 EmotionPredictor，模型路徑：{models_base_path}")
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        print(f"使用設備：{self.device}")
        self.emotions = ['anger', 'disgust', 'fear', 'sadness', 'surprise', 'happiness']
        
        # 初始化狀態變數
        self.last_analysis_time = None
        self.last_analysis_result = None
        self.analyze_lock = False
        self._cached_input = None
        
        # 載入所有模型和tokenizer
        self.models = {}
        self.tokenizers = {}
        
        # 進行更嚴格的模型文件檢查
        missing_models, incomplete_models = self._check_model_files(models_base_path)
        if missing_models or incomplete_models:
            print("警告：存在缺失或不完整的模型：")
            if missing_models:
                print(f"缺失的模型：{missing_models}")
            if incomplete_models:
                for emotion, missing_files in incomplete_models:
                    print(f"{emotion} 模型缺失文件：{missing_files}")
        
        # 載入模型
        for emotion in self.emotions:
            try:
                model_path = os.path.join(models_base_path, emotion)
                if not os.path.exists(model_path):
                    print(f"跳過載入 {emotion} 模型：目錄不存在")
                    continue
                    
                print(f"正在載入 {emotion} 模型...")
                self.models[emotion] = BertForSequenceClassification.from_pretrained(model_path)
                self.models[emotion].to(self.device)
                self.models[emotion].eval()  # 確保模型處於評估模式
                print(f"{emotion} 模型載入成功")
                
                self.tokenizers[emotion] = BertTokenizer.from_pretrained(model_path)
                print(f"{emotion} tokenizer 載入成功")
                
            except Exception as e:
                print(f"載入 {emotion} 模型時發生錯誤：{str(e)}")
                traceback.print_exc()

    def _check_model_files(self, models_base_path):
        missing_models = []
        incomplete_models = []
        required_files = ['config.json', 'pytorch_model.bin', 'tokenizer.json', 'tokenizer_config.json', 'vocab.txt']
        
        for emotion in self.emotions:
            model_path = os.path.join(models_base_path, emotion)
            if not os.path.exists(model_path):
                missing_models.append(emotion)
                continue
                
            files = os.listdir(model_path)
            missing_files = [f for f in required_files if f not in files]
            if missing_files:
                incomplete_models.append((emotion, missing_files))
                
        return missing_models, incomplete_models
    
    def prepare_input(self, text):
        """準備模型輸入數據"""
        if not self.tokenizers:
            raise RuntimeError("沒有可用的 tokenizer")
            
        # 使用第一個可用的 tokenizer
        tokenizer = next(iter(self.tokenizers.values()))
        
        encoding = tokenizer.encode_plus(
            text,
            add_special_tokens=True,
            max_length=256,
            padding='max_length',
            truncation=True,
            return_attention_mask=True,
            return_tensors='pt'
        )
        
        # 確保數據在正確的設備上
        input_ids = encoding['input_ids'].to(self.device)
        attention_mask = encoding['attention_mask'].to(self.device)
        
        return {
            'input_ids': input_ids,
            'attention_mask': attention_mask
        }

    def predict_single(self, text):
        """對單個文本進行情緒預測"""
        current_time = datetime.now()
        
        # 檢查緩存
        if (self.last_analysis_time and 
            (current_time - self.last_analysis_time).total_seconds() < 5 and 
            self.last_analysis_result):
            print("返回緩存結果")
            return self.last_analysis_result
        
        # 檢查鎖
        if self.analyze_lock:
            print("分析器被鎖定，返回默認值")
            return {emotion: 0.0 for emotion in self.emotions}
        
        self.analyze_lock = True
        start_time = time.time()
        results = {}
        successful_emotions = []
        failed_emotions = []
        
        try:
            # 準備輸入
            try:
                prepared_input = self.prepare_input(text)
                print("輸入準備完成")
            except Exception as e:
                print(f"準備輸入時出錯：{str(e)}")
                return {emotion: 0.0 for emotion in self.emotions}
            
            # 對每種情緒進行預測
            for emotion in self.emotions:
                if emotion not in self.models:
                    print(f"跳過 {emotion}: 模型未載入")
                    failed_emotions.append(emotion)
                    results[emotion] = 0.0
                    continue
                    
                try:
                    #emotion_start_time = time.time()
                    
                    with torch.no_grad():
                        outputs = self.models[emotion](
                            input_ids=prepared_input['input_ids'],
                            attention_mask=prepared_input['attention_mask']
                        )
                        probabilities = torch.softmax(outputs.logits, dim=1)
                        results[emotion] = probabilities[0][1].item()
                    
                    #process_time = time.time() - emotion_start_time
                    print(f"{emotion} 分析完成: {results[emotion]:.4f}")
                    successful_emotions.append(emotion)
                    
                except Exception as e:
                    print(f"分析 {emotion} 時出錯: {e}")
                    results[emotion] = 0.0
                    failed_emotions.append(emotion)
            
            if successful_emotions:
                print(f"成功分析的情緒: {successful_emotions}")
            if failed_emotions:
                print(f"分析失敗的情緒: {failed_emotions}")
            
            # 更新緩存
            formatted_results = self._format_response(results)
            self.last_analysis_time = current_time
            self.last_analysis_result = formatted_results
            
            return formatted_results
            
        finally:
            self.analyze_lock = False
            total_time = time.time() - start_time
            print(f"總分析時間: {total_time:.2f}秒")

    def _format_response(self, emotion_scores):
        """格式化情緒分析結果"""
        if not emotion_scores:
            return {
                "emotion": "unknown",
                "emotion_reason": "無法進行情緒分析",
                "reply_suggestions": ["抱歉，我現在無法分析情緒", "讓我們繼續聊天吧"]
            }
            
        # 找出最強情緒
        dominant_emotion = max(emotion_scores.items(), key=lambda x: x[1])
        emotion_name = dominant_emotion[0]
        emotion_score = dominant_emotion[1]
        
        print(f"情緒分數：{emotion_scores}")
        print(f"主導情緒：{emotion_name} (分數：{emotion_score})")
        
        # 生成情緒分析理由
        emotion_reason = f"檢測到的主要情緒是{emotion_name}（信心度：{emotion_score*100:.1f}%）"
        
        # 根據情緒生成回應建議
        suggestions = {
            'anger': [
                "我理解你現在的心情，讓我們冷靜下來討論",
                "你的感受我能理解，我們可以好好談談嗎？"
            ],
            'disgust': [
                "我明白這件事讓你感到不舒服",
                "讓我們試著從不同角度來看這件事"
            ],
            'fear': [
                "不要擔心，有我在這裡陪著你",
                "告訴我你的具體顧慮，我們一起想辦法"
            ],
            'sadness': [
                "我能理解你現在的心情，需要我陪你聊聊嗎？",
                "你現在的感受我明白，要不要多說說看？"
            ],
            'surprise': [
                "這確實很出人意料，你怎麼看？",
                "聽起來很特別，要不要分享更多細節？"
            ],
            'happiness': [
                "真為你感到開心！",
                "太棒了！要不要說說是什麼讓你這麼開心？"
            ]
        }
        
        reply_suggestions = suggestions.get(emotion_name, [
            "謝謝你的分享",
            "我明白了，讓我們繼續聊聊"
        ])
        
        return {
            "emotion": emotion_name,
            "emotion_reason": emotion_reason,
            "reply_suggestions": reply_suggestions
        }

    def load_models(self):
        for emotion in self.emotions:
            try:
                if emotion not in self.models:
                    current_app.logger.error(f"找不到 {emotion} 的模型")
                elif not isinstance(self.models[emotion], BertForSequenceClassification):
                    current_app.logger.error(f"{emotion} 的模型類型不正確")
                else:
                    current_app.logger.info(f"{emotion} 模型正確載入")
            except Exception as e:
                current_app.logger.error(f"檢查 {emotion} 模型時出錯: {str(e)}")


    def _analyze_emotions(self, text):
        results = {}
        # 保存當前應用上下文的引用
        app = current_app._get_current_object()
        
        try:
            prepared_input = self.prepare_input(text)
            app.logger.debug("輸入準備完成")
            
            for emotion in self.emotions:
                emotion_start_time = time.time()
                try:
                    with torch.no_grad():
                        outputs = self.models[emotion](
                            input_ids=prepared_input['input_ids'],
                            attention_mask=prepared_input['attention_mask']
                        )
                        probabilities = torch.softmax(outputs.logits, dim=1)
                        results[emotion] = probabilities[0][1].item()
                        
                    app.logger.debug(
                        f"{emotion}: {results[emotion]:.4f} "
                        f"(耗時: {time.time() - emotion_start_time:.2f}秒)"
                    )
                    
                except Exception as e:
                    app.logger.error(
                        f"分析 {emotion} 時出錯: {str(e)}\n"
                        f"耗時: {time.time() - emotion_start_time:.2f}秒"
                    )
                    results[emotion] = 0.0
            
            return results
        except Exception as e:
            app.logger.error(f"分析情緒時發生錯誤: {str(e)}")
            return {emotion: 0.0 for emotion in self.emotions}

    def predict_batch(self, texts):
        """
        批次預測多個文本的情緒
        """
        all_results = []
        for text in texts:
            result = self.predict_single(text)
            all_results.append(result)
        return all_results

    def predict_message(self, text):
        results = {}
        try:
            prepared_input = self.prepare_input(text)
            
            for emotion in self.emotions:
                if emotion not in self.models:
                    results[emotion] = 0.0
                    continue
                    
                with torch.no_grad():
                    outputs = self.models[emotion](
                        input_ids=prepared_input['input_ids'],
                        attention_mask=prepared_input['attention_mask']
                    )
                    probabilities = torch.softmax(outputs.logits, dim=1)
                    results[emotion] = probabilities[0][1].item()
            
            return results
        except Exception as e:
            print(f"預測情緒時出錯: {str(e)}")
            return {emotion: 0.0 for emotion in self.emotions}

    def analyze_chat_history(self, group_id, time_window=None):
        messages = get_recent_messages(group_id)
        analyses = []
        
        for message in messages:
            if time_window:
                message_time = datetime.fromisoformat(message['timestamp'].replace('Z', '+00:00'))
                if (datetime.now() - message_time).total_seconds() > time_window:
                    continue
                    
            emotion_results = self.predict_message(message['content'])
            analyses.append({
                'sender_id': message['sender_id'],
                'content': message['content'],
                'timestamp': message['timestamp'],
                'emotions': emotion_results
            })
        
        return self._calculate_chat_metrics(analyses)

    def _calculate_chat_metrics(self, analyses):
        if not analyses:
            return {
                'overall_emotions': {emotion: 0 for emotion in self.emotions},
                'emotion_trends': {emotion: [] for emotion in self.emotions},
                'timestamps': [],
                'messages_analyzed': 0
            }

        # 計算整體情緒
        overall_emotions = {emotion: 0 for emotion in self.emotions}
        emotion_trends = {emotion: [] for emotion in self.emotions}
        timestamps = []

        for analysis in analyses:
            timestamps.append(analysis['timestamp'])
            for emotion in self.emotions:
                score = analysis['emotions'][emotion]
                emotion_trends[emotion].append(score)
                overall_emotions[emotion] += score

        # 計算平均值
        for emotion in self.emotions:
            overall_emotions[emotion] /= len(analyses)

        return {
            'overall_emotions': overall_emotions,
            'emotion_trends': emotion_trends,
            'timestamps': timestamps,
            'messages_analyzed': len(analyses)
        }


def format_results(results):
    """格式化預測結果"""
    # 按機率排序情緒
    sorted_emotions = sorted(results.items(), key=lambda x: x[1], reverse=True)

    print("\n預測結果:")
    print("-" * 50)
    for emotion, prob in sorted_emotions:
        prob_percentage = prob * 100
        print(f"{emotion}: {prob_percentage:.2f}%")

    # 找出主要情緒（機率超過閾值）
    main_emotions = [emotion for emotion, prob in sorted_emotions if prob > 0.5]

    if main_emotions:
        print("\n主要情緒:", ", ".join(main_emotions))
    else:
        print("\n沒有檢測到明顯的情緒")

def process_excel_data(file_path, emotion):
    """處理Excel數據，將指定情緒轉換為二分類標籤"""
    df = pd.read_excel(file_path)
    texts = df.iloc[:, 0].values

    # 獲取目標情緒的標籤
    labels = (df[emotion] == 'p1').astype(int).values

    return texts, labels

def train_model(train_dataloader, model, optimizer, device):
    model.train()
    total_loss = 0

    for batch in train_dataloader:
        optimizer.zero_grad()

        input_ids = batch['input_ids'].to(device)
        attention_mask = batch['attention_mask'].to(device)
        labels = batch['labels'].to(device)

        outputs = model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            labels=labels
        )

        loss = outputs.loss
        total_loss += loss.item()

        loss.backward()
        optimizer.step()

    return total_loss / len(train_dataloader)

def evaluate_model(eval_dataloader, model, device):
    model.eval()
    total_correct = 0
    total_samples = 0
    predictions_list = []
    true_labels_list = []

    with torch.no_grad():
        for batch in eval_dataloader:
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            labels = batch['labels'].to(device)

            outputs = model(
                input_ids=input_ids,
                attention_mask=attention_mask
            )

            predictions = torch.argmax(outputs.logits, dim=1)
            predictions_list.extend(predictions.cpu().numpy())
            true_labels_list.extend(labels.cpu().numpy())
            total_correct += (predictions == labels).sum().item()
            total_samples += labels.size(0)

    accuracy = total_correct / total_samples
    return accuracy, predictions_list, true_labels_list

def train_emotion_model(emotion, file_path, output_dir, device, config):
    """針對特定情緒訓練模型"""
    print(f"\n開始訓練 {emotion} 情緒模型...")

    # 創建模型保存目錄
    emotion_output_dir = os.path.join(output_dir, emotion)
    os.makedirs(emotion_output_dir, exist_ok=True)

    # 載入資料
    texts, labels = process_excel_data(file_path, emotion)

    # 分割訓練集和驗證集
    train_texts, val_texts, train_labels, val_labels = train_test_split(
        texts, labels, test_size=0.2, random_state=42
    )

    # 初始化tokenizer和model
    tokenizer = BertTokenizer.from_pretrained('bert-base-chinese')
    model = BertForSequenceClassification.from_pretrained(
        'bert-base-chinese',
        num_labels=2
    ).to(device)

    # 創建datasets
    train_dataset = EmotionDataset(train_texts, train_labels, tokenizer, config['MAX_LEN'])
    val_dataset = EmotionDataset(val_texts, val_labels, tokenizer, config['MAX_LEN'])

    # 創建dataloaders
    train_dataloader = DataLoader(train_dataset, batch_size=config['BATCH_SIZE'], shuffle=True)
    val_dataloader = DataLoader(val_dataset, batch_size=config['BATCH_SIZE'])

    # 設定optimizer
    optimizer = AdamW(model.parameters(), lr=config['LEARNING_RATE'])

    # 訓練模型
    best_accuracy = 0

    for epoch in range(config['EPOCHS']):
        print(f'\nEpoch {epoch + 1}/{config["EPOCHS"]}')

        # 訓練
        train_loss = train_model(train_dataloader, model, optimizer, device)
        print(f'Average training loss: {train_loss:.4f}')

        # 評估
        val_accuracy, predictions, true_labels = evaluate_model(val_dataloader, model, device)
        print(f'Validation accuracy: {val_accuracy:.4f}')

        # 保存最佳模型
        if val_accuracy > best_accuracy:
            best_accuracy = val_accuracy
            model.save_pretrained(emotion_output_dir)
            tokenizer.save_pretrained(emotion_output_dir)
            print(f'New best model saved with accuracy: {best_accuracy:.4f}')

    return best_accuracy

def check_models(self, models_base_path):
    """檢查模型文件的完整性"""
    missing_models = []
    incomplete_models = []
    required_files = ['config.json', 'pytorch_model.bin', 'tokenizer.json', 'tokenizer_config.json', 'vocab.txt']
    
    for emotion in self.emotions:
        model_path = os.path.join(models_base_path, emotion)
        if not os.path.exists(model_path):
            missing_models.append(emotion)
            continue
            
        files = os.listdir(model_path)
        missing_files = [f for f in required_files if f not in files]
        if missing_files:
            incomplete_models.append((emotion, missing_files))
    
    return missing_models, incomplete_models

def analyze_labels(file_path):
    """分析Excel數據中的標籤分布"""
    df = pd.read_excel(file_path)
    emotion_columns = ['anger', 'disgust', 'fear', 'sadness', 'surprise', 'happiness']

    label_stats = {}
    for emotion in emotion_columns:
        p1_count = (df[emotion] == 'p1').sum()
        p0_count = (df[emotion] == 'p0').sum()

        label_stats[emotion] = {
            'p1_count': p1_count,
            'p0_count': p0_count,
            'total': p1_count + p0_count,
            'p1_percentage': (p1_count / (p1_count + p0_count) * 100).round(2)
        }

    print("\n標籤分布統計：")
    print("-" * 50)
    for emotion, stats in label_stats.items():
        print(f"\n{emotion}情緒：")
        print(f"p1數量：{stats['p1_count']}")
        print(f"p0數量：{stats['p0_count']}")
        print(f"總數量：{stats['total']}")
        print(f"p1佔比：{stats['p1_percentage']}%")

    return label_stats

def main():
    # 設定參數
    config = {
        'BATCH_SIZE': 32,
        'EPOCHS': 3,
        'MAX_LEN': 128,
        'LEARNING_RATE': 2e-5
    }

    # 設定檔案路徑和輸出目錄
    file_path = r"C:\MBTI_Chat\test1.xlsx"
    output_dir = 'emotion_models'
    os.makedirs(output_dir, exist_ok=True)

    # 設定設備
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f'Using device: {device}')

    # 分析數據集標籤分布
    print("\n分析數據集標籤分布...")
    label_stats = analyze_labels(file_path)

    # 定義所有情緒
    emotions = ['anger', 'disgust', 'fear', 'sadness', 'surprise', 'happiness']

    # 訓練每個情緒的模型
    results = {}
    for emotion in emotions:
        accuracy = train_emotion_model(emotion, file_path, output_dir, device, config)
        results[emotion] = accuracy

    # 打印最終結果
    print("\n所有模型訓練完成！")
    print("-" * 50)
    print("各情緒模型最佳準確率：")
    for emotion, accuracy in results.items():
        print(f"{emotion}: {accuracy:.4f}")

if __name__ == '__main__':
    main()
    predictor = EmotionPredictor()
    while True:
        print("\n請輸入要分析的文本 (輸入'quit'退出):")
        text = input()

        if text.lower() == 'quit':
            break

        results = predictor.predict_single(text)
        format_results(results)