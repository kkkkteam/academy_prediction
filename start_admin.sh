#!/bin/bash

# 啟動管理員界面腳本

echo "=========================================="
echo "  模型管理系統啟動中..."
echo "=========================================="
echo ""
echo "管理界面將在瀏覽器中自動打開"
echo "如果沒有自動打開，請訪問: http://localhost:8502"
echo ""
echo "按 Ctrl+C 停止服務器"
echo ""

# 設置環境變量來減少關閉時的警告
export PYTHONUNBUFFERED=1

# 啟動 Streamlit 管理界面（使用不同的端口）
# 注意：關閉時的 "Event loop is closed" 警告是無害的，可以忽略
streamlit run admin.py --server.port 8502 --server.headless true
