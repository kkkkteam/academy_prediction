"""
創建示例 eClass 數據文件
"""

import pandas as pd
import numpy as np
from pathlib import Path

# 設置隨機種子以便結果可重現（可選）
np.random.seed(42)

# 學生列表
students = [
    'STU001', 'STU002', 'STU003', 'STU004', 'STU005',
    'STU006', 'STU007', 'STU008', 'STU009', 'STU010'
]

# 科目列表
subjects = [
    'English', 'Chinese', 'Mathematics', 'Science', 'History',
    'Geography', 'Physics', 'Chemistry', 'Biology'
]

# 為每個學生生成不同的能力水平（基礎分數，範圍 50-95）
student_base_scores = {}
for student in students:
    # 每個學生有一個總體能力水平
    base_ability = np.random.normal(70, 20)  # 平均70，標準差20
    base_ability = np.clip(base_ability, 20, 95)  # 限制在20-95之間
    student_base_scores[student] = base_ability

# 為每個科目生成難度係數（某些科目可能較難或較易）
subject_difficulty = {}
for subject in subjects:
    # 科目難度係數，範圍 0.85-1.15
    difficulty = np.random.normal(1.0, 0.1)
    difficulty = np.clip(difficulty, 0.85, 1.15)
    subject_difficulty[subject] = difficulty

# 創建數據字典
# 第一列是 UserLogin（學生ID），用於匹配 HKDSE/IB 結果
# 加入 Grade 欄位示範年級標識（例如 S5）
sample_data = {
    'UserLogin': students,
    'Grade': ['S5'] * len(students),
}

# 為每個科目生成3個Term的成績
for subject in subjects:
    for term in [1, 2, 3]:
        scores = []
        for student in students:
            # 基礎分數 = 學生能力 × 科目難度
            base_score = student_base_scores[student] * subject_difficulty[subject]
            
            # 添加隨機波動
            # Term1: 較大波動（適應期）
            # Term2: 中等波動（穩定期）
            # Term3: 較小波動（熟練期）
            if term == 1:
                noise = np.random.normal(0, 8)  # 標準差8
            elif term == 2:
                noise = np.random.normal(0, 6)  # 標準差6
            else:  # term == 3
                noise = np.random.normal(0, 5)  # 標準差5
            
            # 添加科目特異性波動（某些學生在某些科目表現更好/更差）
            subject_specific = np.random.normal(0, 5)
            
            # 計算最終分數
            final_score = base_score + noise + subject_specific
            
            # 限制在合理範圍內（0-100）
            final_score = np.clip(final_score, 0, 100)
            
            # 四捨五入到整數
            scores.append(round(final_score))
        
        # 添加到數據字典
        col_name = f'{subject}_Term{term}'
        sample_data[col_name] = scores

df = pd.DataFrame(sample_data)

# 保存為 Excel 文件
output_dir = Path("sample_files")
output_dir.mkdir(exist_ok=True)

output_file = output_dir / "sample_eclass_data.xlsx"
df.to_excel(output_file, index=False)

print(f"✓ 示例文件已創建: {output_file}")
print(f"\n文件包含 {len(df)} 個學生的數據")
print(f"包含 {len(df.columns) - 1} 個成績欄位（不包括學生ID）")
print("\n前5行數據預覽:")
print(df.head())
