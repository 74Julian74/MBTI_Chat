import torch
from torch.utils.data import Dataset, DataLoader
from transformers import BertTokenizer, BertForSequenceClassification
import pandas as pd
from sklearn.metrics import confusion_matrix, classification_report
import seaborn as sns
import matplotlib.pyplot as plt
from tqdm import tqdm
import os


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


def evaluate_emotion_model(model_path, test_data_path, emotion):
    """評估特定情緒模型的性能"""
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"使用設備: {device}")

    # 載入模型和tokenizer
    model = BertForSequenceClassification.from_pretrained(model_path).to(device)
    tokenizer = BertTokenizer.from_pretrained(model_path)
    model.eval()

    # 讀取測試數據
    df = pd.read_excel(test_data_path)
    texts = df.iloc[:, 0].values  # 假設第一列是文本
    labels = (df[emotion] == 'p1').astype(int).values

    # 創建dataset和dataloader
    test_dataset = EmotionDataset(texts, labels, tokenizer)
    test_dataloader = DataLoader(test_dataset, batch_size=32, num_workers=4)

    # 進行預測
    all_predictions = []
    all_labels = []

    with torch.no_grad():
        for batch in tqdm(test_dataloader, desc=f'評估 {emotion} 模型'):
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            labels = batch['labels'].to(device)

            outputs = model(input_ids=input_ids, attention_mask=attention_mask)
            predictions = torch.argmax(outputs.logits, dim=1)

            all_predictions.extend(predictions.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())

    # 計算混淆矩陣
    cm = confusion_matrix(all_labels, all_predictions)

    # 計算詳細指標
    report = classification_report(all_labels, all_predictions)

    # 繪製混淆矩陣熱圖
    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
    plt.title(f'Confusion Matrix - {emotion}')
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.savefig(f'confusion_matrix_{emotion}.png')
    plt.close()

    # 計算評估指標
    tn, fp, fn, tp = cm.ravel()
    accuracy = (tp + tn) / (tp + tn + fp + fn)
    precision = tp / (tp + fp) if (tp + fp) != 0 else 0
    recall = tp / (tp + fn) if (tp + fn) != 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) != 0 else 0

    # 打印結果
    print(f"\n{emotion} 模型評估結果:")
    print("-" * 50)
    print(f"Accuracy: {accuracy:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall: {recall:.4f}")
    print(f"F1 Score: {f1:.4f}")
    print("\n混淆矩陣:")
    print(f"True Negative: {tn}")
    print(f"False Positive: {fp}")
    print(f"False Negative: {fn}")
    print(f"True Positive: {tp}")
    print("\n分類報告:")
    print(report)


def main():
    # 設定路徑
    models_base_path = 'C:/Users/user/Desktop/bert/emotion_models'
    test_data_path = 'C:/Users/user/Desktop/matrix.xlsx'  # 替換成你的測試數據路徑

    # 所有情緒
    emotions = ['anger', 'disgust', 'fear', 'sadness', 'surprise', 'happiness']

    # 評估每個情緒模型
    for emotion in emotions:
        model_path = os.path.join(models_base_path, emotion)
        print(f"\n評估 {emotion} 模型...")
        evaluate_emotion_model(model_path, test_data_path, emotion)

        # 清理GPU記憶體
        if torch.cuda.is_available():
            torch.cuda.empty_cache()


if __name__ == '__main__':
    main()