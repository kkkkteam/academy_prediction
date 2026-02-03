"""
創建示例 eClass 數據文件
"""

import pandas as pd
import numpy as np
from pathlib import Path

# 創建示例數據 - 模擬真實的 eClass 數據格式
# 第一列是學生ID，後續列是各科目的成績

sample_data = {
    'Student_ID': [
        'STU001', 'STU002', 'STU003', 'STU004', 'STU005',
        'STU006', 'STU007', 'STU008', 'STU009', 'STU010'
    ],
    'English_Term1': [75, 82, 68, 90, 73, 85, 78, 72, 88, 80],
    'English_Term2': [78, 85, 70, 92, 76, 87, 81, 75, 90, 83],
    'English_Term3': [80, 88, 72, 94, 78, 89, 84, 77, 92, 85],
    'Chinese_Term1': [80, 78, 72, 85, 76, 82, 79, 74, 86, 81],
    'Chinese_Term2': [82, 80, 74, 87, 78, 84, 81, 76, 88, 83],
    'Chinese_Term3': [85, 83, 77, 90, 81, 87, 84, 79, 91, 86],
    'Mathematics_Term1': [88, 85, 70, 92, 80, 90, 83, 75, 93, 87],
    'Mathematics_Term2': [90, 87, 72, 94, 82, 92, 85, 77, 95, 89],
    'Mathematics_Term3': [92, 89, 74, 96, 84, 94, 87, 79, 97, 91],
    'Science_Term1': [82, 79, 75, 88, 77, 85, 80, 73, 89, 82],
    'Science_Term2': [84, 81, 77, 90, 79, 87, 82, 75, 91, 84],
    'Science_Term3': [86, 83, 79, 92, 81, 89, 84, 77, 93, 86],
    'History_Term1': [78, 81, 68, 85, 74, 83, 77, 71, 87, 79],
    'History_Term2': [80, 83, 70, 87, 76, 85, 79, 73, 89, 81],
    'History_Term3': [82, 85, 72, 89, 78, 87, 81, 75, 91, 83],
    'Geography_Term1': [80, 83, 72, 87, 79, 86, 79, 73, 88, 81],
    'Geography_Term2': [82, 85, 74, 89, 81, 88, 81, 75, 90, 83],
    'Geography_Term3': [84, 87, 76, 91, 83, 90, 83, 77, 92, 85],
    'Physics_Term1': [85, 80, 73, 90, 78, 88, 82, 76, 91, 84],
    'Physics_Term2': [87, 82, 75, 92, 80, 90, 84, 78, 93, 86],
    'Physics_Term3': [89, 84, 77, 94, 82, 92, 86, 80, 95, 88],
    'Chemistry_Term1': [83, 77, 70, 88, 75, 86, 79, 73, 89, 82],
    'Chemistry_Term2': [85, 79, 72, 90, 77, 88, 81, 75, 91, 84],
    'Chemistry_Term3': [87, 81, 74, 92, 79, 90, 83, 77, 93, 86],
    'Biology_Term1': [81, 79, 74, 86, 76, 84, 78, 72, 87, 80],
    'Biology_Term2': [83, 81, 76, 88, 78, 86, 80, 74, 89, 82],
    'Biology_Term3': [85, 83, 78, 90, 80, 88, 82, 76, 91, 84],
    'Average_Score': [82.3, 82.7, 73.5, 89.8, 78.6, 87.2, 81.4, 75.2, 90.6, 83.8]
}

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
