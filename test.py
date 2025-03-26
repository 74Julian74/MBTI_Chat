import torch

# 確認 CUDA 是否可用
print("CUDA 可用性：", torch.cuda.is_available())

# 列出可用的 GPU 設備數量
print("可用的 GPU 數量：", torch.cuda.device_count())

# 獲取當前 GPU 名稱
if torch.cuda.is_available():
    print("當前 GPU 名稱：", torch.cuda.get_device_name(0))
