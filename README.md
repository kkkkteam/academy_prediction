# 學生成績預測系統

這是一個基於機器學習的學生成績預測系統，可以根據學生的 eClass 數據預測他們的 HKDSE 或 IB 考試結果。

## 功能特點

- 📊 **數據分析**：自動分析 eClass、HKDSE、IB 數據
- 🤖 **機器學習模型**：使用 XGBoost 進行預測
- 🎨 **Web 界面**：友好的 Streamlit Web UI
- 📈 **預測結果**：提供詳細的預測結果和等級解釋

## 安裝步驟

### 1. 安裝依賴

```bash
# 使用虛擬環境（推薦）
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安裝所有依賴
pip install -r requirements.txt
```

### 2. 準備數據

確保你的數據文件結構如下：

```
Data/
├── eClass Data/
│   ├── 2017-2018 S3 YEARLY_converted.xlsx
│   ├── 2018-2019 S3 YEARLY_converted.xlsx
│   └── ...
├── HKDSE/
│   ├── 2021-2022/
│   │   └── Logos-HKDSE-2021-2022-V1.2.xls
│   └── ...
└── IB/
    ├── IB_Result_2022_Entry_v4_20220705_ENTRY_AfterEUR.xlsx
    └── ...
```

## 使用方法

### 步驟 1：訓練模型

首先需要訓練預測模型：

```bash
# 訓練 HKDSE 模型
python train_model.py --target hkdse --data-dir ./Data

# 訓練 IB 模型
python train_model.py --target ib --data-dir ./Data

# 或同時訓練兩個模型
python train_model.py --target both --data-dir ./Data
```

訓練完成後，模型會保存在 `./models/` 目錄下：
- `hkdse_model.pkl`
- `ib_model.pkl`

### 步驟 2：啟動 Web UI

```bash
streamlit run app.py
```

瀏覽器會自動打開，或者訪問 `http://localhost:8501`

### 步驟 3：使用 Web UI 進行預測

1. 在左側選擇預測目標（HKDSE 或 IB）
2. **下載示例文件**（確保數據格式正確）
3. 上傳學生的 eClass 數據文件（Excel 格式）
4. 點擊「開始預測」按鈕
5. 查看預測結果和下載結果

### 數據格式要求

- **第一列**：學生ID（文字或數字）
- **後續列**：各科目成績（數值，0-100）
- 支持格式：`.xlsx`, `.xls`, `.csv`

**示例文件位置**：`sample_files/sample_eclass_data.xlsx`

你可以在 Web UI 中直接下載示例文件，或查看 `sample_files/README.md` 了解詳細格式說明。

## 命令行使用

你也可以使用命令行進行預測：

```bash
# 預測 HKDSE 結果
python predict_model.py --mode predict --target hkdse --input <eClass數據文件>

# 預測 IB 結果
python predict_model.py --mode predict --target ib --input <eClass數據文件>

# 評估模型
python predict_model.py --mode evaluate --target hkdse
```

## 數據分析

使用 `analysis.py` 進行數據探索性分析：

```bash
# 分析所有數據
python analysis.py --input ./Data

# 分析特定文件
python analysis.py --input ./Data/eClass\ Data/2017-2018\ S3\ YEARLY_converted.xlsx
```

## 項目結構

```
Program/
├── analysis.py          # 數據分析工具
├── predict_model.py     # 預測模型核心代碼
├── train_model.py       # 模型訓練腳本
├── app.py               # Streamlit Web UI
├── requirements.txt     # Python 依賴
├── README.md           # 本文件
├── Data/               # 數據目錄
│   ├── eClass Data/
│   ├── HKDSE/
│   └── IB/
├── sample_files/       # 示例文件
│   ├── sample_eclass_data.xlsx  # eClass 數據格式示例
│   └── README.md       # 示例文件說明
└── models/             # 訓練好的模型（自動生成）
    ├── hkdse_model.pkl
    └── ib_model.pkl
```

## 技術棧

- **Python 3.7+**
- **XGBoost**：梯度提升機器學習模型
- **scikit-learn**：機器學習工具庫
- **pandas**：數據處理
- **Streamlit**：Web UI 框架
- **matplotlib/seaborn**：數據可視化

## 注意事項

1. **數據格式**：確保 eClass 數據文件格式正確，第一列應為學生ID
2. **模型訓練**：首次使用前必須先訓練模型
3. **學生ID匹配**：如果 eClass 和 HKDSE/IB 的學生ID格式不同，系統會嘗試多種匹配方式
4. **預測準確性**：預測結果僅供參考，實際成績可能因多種因素而有所不同

## 故障排除

### 問題：無法讀取 .xls 文件

```bash
pip install xlrd>=2.0.1
```

### 問題：模型訓練時無法匹配學生數據

系統會自動嘗試多種匹配方式。如果仍然失敗，請檢查：
- 學生ID格式是否一致
- 數據文件是否完整

### 問題：Streamlit 無法啟動

```bash
# 確保已安裝 Streamlit
pip install streamlit>=1.28.0

# 檢查端口是否被占用
streamlit run app.py --server.port 8502
```

## 授權

本項目僅供教育用途。

## 聯繫方式

如有問題或建議，請聯繫項目維護者。
