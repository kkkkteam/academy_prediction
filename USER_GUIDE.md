# Student Performance Prediction System — User Guide

**學生成績預測系統 — 使用說明**

---

## 1. Accessing the system / 如何進入系統

- Open the link provided by the school (e.g. Streamlit Cloud or your school server).
- Use the **language switcher** (top-right) to switch between 中文 and English.

---

## 2. Main pages / 主要頁面

The app has **two tabs** in the left sidebar:

| Tab 分頁 | Purpose 用途 |
|----------|----------------|
| **學生成績預測 / Score Prediction** | Upload eClass data and view HKDSE or IB predictions. 上傳 eClass 數據並查看預測結果。 |
| **訓練模型 / Train Model** | Upload training data and train or update models. **Password required.** 上傳訓練數據並訓練模型，需密碼。 |

Most teachers only need the **Prediction** tab.  
大部分老師只需使用「預測」分頁。

---

## 3. How to run a prediction / 如何進行預測

1. Select **學生成績預測 / Score Prediction** (left sidebar).
2. Choose **HKDSE** or **IB** as the prediction target.
3. **Download the sample file** (optional) to check the required format.
4. **Upload** your eClass Excel file (`.xlsx` or `.xls`).
5. The system will show a **data check** (preview and basic validation). Review it, then click **開始預測 / Start Prediction**.
6. View the **overview table** and **per-student, per-subject** results. You can **download the results as CSV**.

**Data check:** The system shows the first few rows and checks that scores are in the 0–100 range. If there are issues, fix your file and upload again.

---

## 4. What-if simulation / What-if 模擬（按科目）

After a prediction is done, scroll down to **What-if 模擬（按科目）**:

- **Select a student** and **select a subject**.
- Use the **slider** to change the eClass score for that subject.
- The system shows **original prediction**, **simulated prediction**, and **change**.

This helps answer: “If this student’s score in this subject were higher/lower, how would the predicted grade change?”

---

## 5. Data format for prediction / 預測用數據格式

- **First column:** UserLogin (student ID).
- **Optional second column:** English Name (for display).
- **Other columns:** Subject scores, **numeric 0–100**. You can use multiple terms (e.g. English Term1, Term2, Term3); the system merges them by subject.
- **Not taken:** Use **"--"** for subjects a student did not take.
- **Grade column (optional):** You can include a **Grade** column (e.g. S3, S4, S5, S6, MOCK) in the Excel; the system uses it for reference.

Supported formats: `.xlsx`, `.xls`, `.csv`.

---

## 6. Train Model page / 訓練模型頁面

- **Password required.** Contact the administrator if you need access.
- On that page you can:
  - Upload eClass data and HKDSE/IB result files.
  - Train or update the HKDSE and/or IB models.
  - Download the trained model files (`.pkl`) or download **sample files** (eClass, HKDSE, IB) to see the expected format.
- **Change password:** Use the “更改密碼 / Change password” section (current password + new password twice).

---

## 7. Quick tips / 使用提示

- Use the **sample file** to ensure your Excel structure matches.
- If the data check shows values outside 0–100, correct the source file before predicting.
- Predictions are **by subject**; each subject’s eClass average is used for that subject’s predicted grade.
- For the demo, if you do not have real data, use the provided sample eClass file to try the full flow (upload → data check → prediction → What-if).

---

## 8. Support / 支援

If you have questions about data format, access, or the Train Model password, please contact your school’s system administrator or the person who sent you this guide.

---

*Student Performance Prediction System — Demo User Guide*
