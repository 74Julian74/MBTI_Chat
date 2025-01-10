import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QTextEdit,
                             QFileDialog, QProgressBar)
from PyQt5.QtCore import Qt
import torch
from transformers import BertTokenizer, BertForSequenceClassification
import pandas as pd
from sklearn.metrics import confusion_matrix, classification_report
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import numpy as np


class BacktestApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = None
        self.tokenizer = None

    def initUI(self):
        self.setWindowTitle('模型回測工具')
        self.setGeometry(100, 100, 1200, 800)

        # 主要佈局
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        # 上方控制面板
        control_panel = QHBoxLayout()

        # 選擇模型按鈕
        self.model_btn = QPushButton('選擇模型資料夾')
        self.model_btn.clicked.connect(self.select_model)
        control_panel.addWidget(self.model_btn)

        # 選擇數據按鈕
        self.file_btn = QPushButton('選擇測試數據')
        self.file_btn.clicked.connect(self.select_file)
        control_panel.addWidget(self.file_btn)

        # 開始回測按鈕
        self.test_btn = QPushButton('開始回測')
        self.test_btn.clicked.connect(self.start_backtest)
        self.test_btn.setEnabled(False)
        control_panel.addWidget(self.test_btn)

        layout.addLayout(control_panel)

        # 進度條
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        # 路徑顯示
        self.path_label = QLabel('模型路徑: \n數據路徑: ')
        layout.addWidget(self.path_label)

        # 結果顯示區域
        results_layout = QHBoxLayout()

        # 左側報表區域
        self.report_text = QTextEdit()
        self.report_text.setReadOnly(True)
        results_layout.addWidget(self.report_text)

        # 右側混淆矩陣圖
        self.figure, self.ax = plt.subplots(figsize=(6, 6))
        self.canvas = FigureCanvas(self.figure)
        results_layout.addWidget(self.canvas)

        layout.addLayout(results_layout)

        self.model_path = None
        self.file_path = None

    def select_model(self):
        model_dir = QFileDialog.getExistingDirectory(self, '選擇模型資料夾')
        if model_dir:
            self.model_path = model_dir
            self.update_path_label()
            self.check_ready()

    def select_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, '選擇Excel文件', '', 'Excel Files (*.xlsx *.xls)')
        if file_name:
            self.file_path = file_name
            self.update_path_label()
            self.check_ready()

    def update_path_label(self):
        self.path_label.setText(f'模型路徑: {self.model_path or "未選擇"}\n數據路徑: {self.file_path or "未選擇"}')

    def check_ready(self):
        self.test_btn.setEnabled(bool(self.model_path and self.file_path))

    def start_backtest(self):
        try:
            # 載入模型和tokenizer
            self.model = BertForSequenceClassification.from_pretrained(self.model_path).to(self.device)
            self.tokenizer = BertTokenizer.from_pretrained(self.model_path)
            self.model.eval()

            # 讀取數據
            df = pd.read_excel(self.file_path)
            # 確保文本欄位是字串型別
            texts = df.iloc[:, 0].astype(str).tolist()

            # 從模型路徑獲取情緒名稱
            emotion = self.model_path.split('/')[-1].split('\\')[-1]  # 同時處理 / 和 \
            labels = (df[emotion] == 'p1').astype(int).values

            # 進行預測
            predictions = []
            batch_size = 32
            total_batches = (len(texts) + batch_size - 1) // batch_size

            for i in range(0, len(texts), batch_size):
                # 更新進度條
                progress = int((i / len(texts)) * 100)
                self.progress_bar.setValue(progress)

                batch_texts = texts[i:i + batch_size]

                # 確保每個文本都是字串
                batch_texts = [str(text).strip() for text in batch_texts]

                try:
                    encodings = self.tokenizer(
                        batch_texts,
                        padding=True,
                        truncation=True,
                        max_length=128,
                        return_tensors='pt'
                    )

                    input_ids = encodings['input_ids'].to(self.device)
                    attention_mask = encodings['attention_mask'].to(self.device)

                    with torch.no_grad():
                        outputs = self.model(input_ids=input_ids, attention_mask=attention_mask)
                        batch_predictions = torch.argmax(outputs.logits, dim=1)
                        predictions.extend(batch_predictions.cpu().numpy())

                except Exception as e:
                    print(f"Error processing batch {i // batch_size}: {str(e)}")
                    print(f"Problem text: {batch_texts}")
                    continue

            self.progress_bar.setValue(100)

            # 計算評估指標
            predictions = np.array(predictions)
            labels = labels[:len(predictions)]  # 確保長度匹配

            cm = confusion_matrix(labels, predictions)
            report = classification_report(labels, predictions, output_dict=True)

            # 顯示結果
            self.show_results(cm, report, emotion)

        except Exception as e:
            self.report_text.setText(f'錯誤: {str(e)}')
            import traceback
            print(traceback.format_exc())

        finally:
            # 清理GPU記憶體
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

    def show_results(self, cm, report, emotion):
        # 顯示報告
        text = f"模型評估報告 ({emotion}):\n\n"
        text += f"準確率 (Accuracy): {report['accuracy']:.4f}\n\n"
        text += f"分類別評估:\n"
        text += f"非{emotion}(0):\n"
        text += f"  精確率: {report['0']['precision']:.4f}\n"
        text += f"  召回率: {report['0']['recall']:.4f}\n"
        text += f"  F1-score: {report['0']['f1-score']:.4f}\n"
        text += f"  支持度: {report['0']['support']}\n\n"
        text += f"{emotion}(1):\n"
        text += f"  精確率: {report['1']['precision']:.4f}\n"
        text += f"  召回率: {report['1']['recall']:.4f}\n"
        text += f"  F1-score: {report['1']['f1-score']:.4f}\n"
        text += f"  支持度: {report['1']['support']}\n"

        self.report_text.setText(text)

        # 繪製混淆矩陣
        self.ax.clear()
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=self.ax)
        self.ax.set_title(f'混淆矩陣 - {emotion}')
        self.ax.set_ylabel('實際類別')
        self.ax.set_xlabel('預測類別')

        emotion_labels = {
            'anger': ['非生氣', '生氣'],
            'disgust': ['非厭惡', '厭惡'],
            'fear': ['非恐懼', '恐懼'],
            'happiness': ['非快樂', '快樂'],
            'sadness': ['非難過', '難過'],
            'surprise': ['非驚訝', '驚訝']
        }

        # 獲取對應的標籤
        labels = emotion_labels.get(emotion, [f'非{emotion}', emotion])

        # 設置x軸和y軸的標籤
        self.ax.set_xticklabels(labels)
        self.ax.set_yticklabels(labels)
        self.canvas.draw()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = BacktestApp()
    ex.show()
    sys.exit(app.exec_())