# 部署到 Streamlit Community Cloud

## 重要：訓練只能在本機做

Streamlit Community Cloud **不會**在雲端幫你訓練模型，因為：

- 雲端沒有你的 `Data/` 資料夾（訓練資料不應上傳到 GitHub，涉及個資與機密）
- 雲端只會執行 `streamlit run app.py`，不會執行 `train_model.py`

所以流程是：**在本機訓練 → 把訓練好的模型檔放進 Git → 再部署**，雲端就會載入這些模型來做預測。

---

## 一、本機訓練（在你自己的電腦上）

### 1. 準備訓練資料夾結構

在專案目錄下建立 `Data` 資料夾，結構如下：

```
Program/
├── Data/
│   ├── eClass Data/     ← 放 eClass 匯出的成績檔（.xlsx / .xls）
│   ├── HKDSE/           ← 放 HKDSE 成績結果檔（.xlsx / .xls）
│   └── IB/              ← 放 IB 成績結果檔（.xlsx / .xls）
├── models/              ← 訓練完成後會在這裡產生 .pkl
├── app.py
├── train_model.py
└── ...
```

- **eClass Data**：從 eClass 匯出的科目成績 Excel，用來當「輸入特徵」。
- **HKDSE**、**IB**：真實的 HKDSE/IB 成績 Excel，用來當「預測目標」；訓練時會和 eClass 的學生做對應。

### 2. 在本機執行訓練

在終端機進入專案目錄後執行：

```bash
# 訓練 HKDSE 與 IB 兩個模型（預設 --data-dir 為 ./Data）
python train_model.py --target both --data-dir ./Data
```

若只訓練其中一個：

```bash
python train_model.py --target hkdse --data-dir ./Data
python train_model.py --target ib --data-dir ./Data
```

訓練成功後，會在 `models/` 下產生：

- `models/hkdse_model.pkl`
- `models/ib_model.pkl`

（以及既有的 `*_model_metrics.json`）

### 3. 確認模型檔存在

```bash
ls -la models/
# 應看到 hkdse_model.pkl、ib_model.pkl
```

---

## 二、把模型放進 Git（讓 Cloud 能用到）

專案已設定為**允許** `models/*.pkl` 提交到 Git（其餘 `.pkl` 仍被忽略）。

在本機執行：

```bash
git add models/hkdse_model.pkl models/ib_model.pkl
git status   # 確認有這兩個檔案
git commit -m "Add trained models for Streamlit Cloud deployment"
git push origin master
```

這樣 GitHub 上就會有這兩個模型檔，部署時 Streamlit Cloud 會一併拉下來。

---

## 三、在 Streamlit Community Cloud 部署

1. 打開 [share.streamlit.io](https://share.streamlit.io)，用 GitHub 登入。
2. 點 **New app**。
3. 選擇你的 **Repository**、**Branch**（例如 `master`）。
4. **Main file path** 填：`app.py`。
5. 若專案不在根目錄，**App URL** 可自訂。
6. 點 **Deploy**。

部署完成後，打開給你的網址，側邊欄應顯示「HKDSE 模型已就緒」「IB 模型已就緒」，即可上傳 eClass 檔案做預測。

---

## 四、之後要更新模型

1. 在本機更新 `Data/` 裡的資料（例如新一屆成績）。
2. 本機再跑一次：`python train_model.py --target both --data-dir ./Data`。
3. 提交並推送新的 `.pkl`：
   ```bash
   git add models/hkdse_model.pkl models/ib_model.pkl
   git commit -m "Update trained models"
   git push
   ```
4. Streamlit Cloud 會自動偵測到 push，重新部署並載入新模型。

---

## 常見問題

**Q: 我不想把模型檔放在 GitHub 可以嗎？**  
A: 可以，但 Streamlit Community Cloud 就無法自動載入模型，需要改用其他部署方式（例如自架主機、或把模型放在雲端儲存再在程式裡下載）。一般校內使用、模型不大時，直接提交 `models/*.pkl` 最簡單。

**Q: 訓練時報錯「找不到資料」？**  
A: 檢查 `Data/eClass Data/`、`Data/HKDSE/`、`Data/IB/` 是否存在，且裡面有對應的 xlsx/xls 檔；並確認 `train_model.py` 的 `--data-dir` 是否指到正確的 `Data` 路徑。

**Q: 部署後側邊欄仍顯示「模型未就緒」？**  
A: 代表雲端沒有讀到 `.pkl`。請確認已把 `models/hkdse_model.pkl` 和 `models/ib_model.pkl` 加入 Git 並 push 到 GitHub，且 `.gitignore` 裡有 `!models/*.pkl`（專案已包含此設定）。
