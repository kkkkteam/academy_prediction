# 示例文件說明

## sample_eclass_data.xlsx

這是 eClass 數據文件的示例格式，供學生參考以確保上傳的數據格式正確。

### 文件格式要求

1. **第一列必須是 UserLogin（學生ID）**
   - 這是用於匹配 HKDSE/IB 結果的學生ID
   - 可以是文字或編碼（如：D1VwXmVbXwc= 或 STU001）
   - 每行代表一個學生
   - **重要**：UserLogin 是學生ID，用於與 HKDSE/IB 數據匹配

2. **第二列可以是 English Name（可選，用於顯示）**
   - 如果沒有，系統會使用 UserLogin 作為顯示名稱
   - 這只是用於界面顯示，不影響匹配

3. **後續列為各科目成績**
   - 必須是數值（0-100）
   - **可以包含多個學期（Term）的成績**，例如：
     - `English Term1`, `English Term2`, `English Term3` 等
     - 系統會自動將同一科目的多個Term成績合併為該科目的平均分
   - 可以包含不同科目的成績
   - **如果學生未修讀某科目，請使用 "--" 標記**

4. **支持的格式**
   - Excel 格式：`.xlsx` 或 `.xls`
   - CSV 格式：`.csv`

### 學期（Term）說明

- **Term 是學期的意思，不是科目分類**
- 例如：
  - `English Term1` = English 科目的第一學期
  - `English Term2` = English 科目的第二學期
  - `Chinese Term1` = Chinese 科目的第一學期
- **系統會自動將同一科目的多個Term成績合併**，計算該科目的平均分
- 預測結果按科目顯示，不按Term分開

### 年級標識說明

文件名或科目名稱中可能包含以下標識：
- **S3**: 三年級（Form 3）
- **S4**: 四年級（Form 4）
- **S5**: 五年級（Form 5）
- **S6**: 六年級（Form 6）
- **MOCK**: 模擬公開試（Mock Examination）

這些標識會自動識別，用於區分不同年級的成績數據。

### 示例文件內容

示例文件包含：
- **10個學生**的示例數據
- **27個成績欄位**（不包括UserLogin列）
- 包含多個科目和多個學期的成績：
  - English (Term 1, 2, 3)
  - Chinese (Term 1, 2, 3)
  - Mathematics (Term 1, 2, 3)
  - Science (Term 1, 2, 3)
  - History (Term 1, 2, 3)
  - Geography (Term 1, 2, 3)
  - Physics (Term 1, 2, 3)
  - Chemistry (Term 1, 2, 3)
  - Biology (Term 1, 2, 3)

### 使用說明

1. 下載 `sample_eclass_data.xlsx`
2. 打開文件查看格式
3. 按照相同格式準備你的數據
4. 在 Web UI 中上傳你的數據文件

### 注意事項

- **第一列必須是 UserLogin（學生ID）**，用於匹配 HKDSE/IB 結果
- 成績必須是數值（0-100），不能是文字
- **未修讀的科目請使用 "--" 標記**（不要用空值或 0）
- 列名可以是任何文字，但第一列必須是 UserLogin
- 數據越多，預測結果可能越準確
- 系統會自動識別 S3、S4、S5、S6、MOCK 等年級標識

### 常見問題

**Q: 我的數據格式與示例不同怎麼辦？**
A: 只要確保第一列是 UserLogin（學生ID），後續列是數值成績即可。列名可以不同。

**Q: UserLogin 和 HKDSE/IB 的 Code 如何匹配？**
A: 系統會嘗試多種匹配方式：
1. 直接匹配（如果格式相同）
2. 順序匹配（按數據順序）
3. 統計特徵匹配（按成績分布）

**Q: 可以只上傳一個學生的數據嗎？**
A: 可以，但建議包含多個學生的數據以獲得更好的預測效果。

**Q: 成績範圍必須是0-100嗎？**
A: 建議使用0-100的標準分數，但系統會自動處理不同範圍的數值。
