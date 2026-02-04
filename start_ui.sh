#!/bin/bash
# 快速啟動 Web UI 腳本

echo "🚀 啟動學生成績預測系統 Web UI..."
echo ""

# 檢查虛擬環境
if [ -d ".venv" ]; then
    echo "✓ 找到虛擬環境，正在啟動..."
    source .venv/bin/activate
else
    echo "⚠️  未找到虛擬環境，使用系統 Python"
fi

# 檢查模型是否存在
if [ ! -f "models/hkdse_model.pkl" ] && [ ! -f "models/ib_model.pkl" ]; then
    echo ""
    echo "⚠️  警告：未找到訓練好的模型！"
    echo "   請先運行以下命令訓練模型："
    echo "   python train_model.py --target both"
    echo ""
    read -p "是否現在訓練模型？(y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        python train_model.py --target both
    fi
fi

# 設置環境變量來減少關閉時的警告
export PYTHONUNBUFFERED=1

# 啟動 Streamlit
echo ""
echo "🌐 正在啟動 Web UI..."
echo "   瀏覽器將自動打開，或訪問 http://localhost:8501"
echo ""
# 注意：關閉時的 "Event loop is closed" 警告是無害的，可以忽略
streamlit run app.py
