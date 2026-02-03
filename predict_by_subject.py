"""
按科目預測模型 - 支持按科目分別預測並顯示結果

支持：
- 使用 English name 作為主鍵
- 按科目分別預測
- 處理 "--" 表示未修讀的情況
- 識別 S3, S4, S5, S6, MOCK 等年級標識
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional
from predict_model import DataPreprocessor, PredictionModel
import pickle


class SubjectBasedPredictor:
    """按科目預測器"""
    
    def __init__(self, target: str = 'hkdse'):
        self.target = target
        self.preprocessor = DataPreprocessor()
        self.models = {}  # 每個科目一個模型
        self.subject_names = []
        
    def load_eclass_data_detailed(self, file_path: Path) -> pd.DataFrame:
        """詳細載入 eClass 數據，保留科目信息"""
        try:
            # 嘗試使用標準格式（有列名）
            try:
                df = pd.read_excel(file_path)
                # 檢查是否有UserLogin列（學生ID）
                if 'UserLogin' in df.columns:
                    # 標準格式，UserLogin是學生ID
                    # 嘗試找到English Name列（可能在第二列或其他列）
                    english_name_col = None
                    for col in df.columns:
                        if col.lower() in ['english_name', 'english name', 'name']:
                            english_name_col = col
                            break
                    
                    # 如果沒有English Name列，使用UserLogin作為顯示名稱
                    if english_name_col:
                        df['English_Name'] = df[english_name_col]
                    else:
                        df['English_Name'] = df['UserLogin']
                    
                    df['Student_ID'] = df['UserLogin']  # UserLogin是學生ID
                    
                    # 處理 "--" 表示未修讀
                    for col in df.columns:
                        if col not in ['UserLogin', 'English_Name', 'Student_ID']:
                            df[col] = df[col].replace('--', None)
                            df[col] = df[col].replace('', None)
                    
                    # 按科目合併Term成績
                    df_merged = self._merge_term_scores(df)
                    return df_merged
                # 檢查是否有English_Name或Student_ID列（舊格式兼容）
                elif 'English_Name' in df.columns or 'English Name' in df.columns:
                    # 標準格式，需要按科目合併Term
                    if 'English_Name' not in df.columns:
                        df = df.rename(columns={'English Name': 'English_Name'})
                    if 'Student_ID' not in df.columns:
                        df['Student_ID'] = df['English_Name']
                    # 添加UserLogin列（使用Student_ID）
                    df['UserLogin'] = df['Student_ID']
                    
                    # 處理 "--" 表示未修讀
                    for col in df.columns:
                        if col not in ['English_Name', 'Student_ID', 'UserLogin']:
                            df[col] = df[col].replace('--', None)
                            df[col] = df[col].replace('', None)
                    
                    # 按科目合併Term成績
                    df_merged = self._merge_term_scores(df)
                    return df_merged
            except:
                pass
            
            # 如果標準格式失敗，使用原始解析方式
            df = pd.read_excel(file_path, header=None)
            
            # 第一行通常是標題行（科目名稱）
            # 第二行可能是 "UserLogin" 或其他標題
            # 從第三行開始是實際數據
            
            # 提取科目名稱（從第一行或第二行）
            subject_columns = {}
            header_row = 0
            
            # 嘗試找到科目名稱行
            for row_idx in range(min(3, len(df))):
                row_data = df.iloc[row_idx]
                # 檢查是否包含科目關鍵字
                subject_count = 0
                for col_idx, val in enumerate(row_data):
                    if pd.notna(val):
                        val_str = str(val).lower()
                        if any(keyword in val_str for keyword in 
                               ['english', 'chinese', 'math', 'science', 'history', 
                                'geography', 'physics', 'chemistry', 'biology', 'term',
                                's3', 's4', 's5', 's6', 'mock']):
                            subject_count += 1
                            if col_idx not in subject_columns:
                                # 保留完整名稱（包含Term信息），稍後會按科目合併
                                subject_name = str(val)
                                subject_columns[col_idx] = subject_name
                
                if subject_count > 5:  # 如果找到多個科目，這可能是標題行
                    header_row = row_idx
                    break
            
            # 構建數據記錄
            records = []
            start_data_row = header_row + 1
            
            for row_idx in range(start_data_row, len(df)):
                row = df.iloc[row_idx]
                
                # 獲取 UserLogin（第一列，這是學生ID）
                userlogin = str(row.iloc[0]) if pd.notna(row.iloc[0]) else None
                
                if not userlogin or userlogin in ['UserLogin', '--', '']:
                    continue
                
                # 嘗試獲取 English name（可能在第二列或其他列）
                english_name = None
                if len(row) > 1:
                    # 檢查第二列是否可能是English name
                    second_col = str(row.iloc[1]) if pd.notna(row.iloc[1]) else None
                    # 如果第二列不是數字且不是Class/No.等標題，可能是English name
                    if second_col and second_col not in ['Class', 'No.', '--']:
                        try:
                            float(second_col)  # 如果是數字，不是English name
                        except:
                            english_name = second_col
                
                # 如果沒有找到English name，使用UserLogin作為顯示名稱
                if not english_name:
                    english_name = userlogin
                
                record = {
                    'english_name': english_name,
                    'student_id': userlogin  # 使用 UserLogin 作為學生ID（用於匹配）
                }
                
                # 提取各科目成績（按科目匯總，不按Term分開）
                subject_scores = {}  # {科目名: [成績列表]}
                
                for col_idx in range(1, min(len(row), 50)):
                    val = row.iloc[col_idx]
                    
                    # 獲取科目名稱（可能包含Term信息，如 "English Term1"）
                    full_name = subject_columns.get(col_idx, f'Subject_{col_idx}')
                    
                    # 提取科目名稱（去掉Term部分）
                    # 例如 "English Term1" -> "English", "Chinese_Term2" -> "Chinese"
                    import re
                    # 去掉 "Term1", "Term2", "Term3", "Term4" 等，以及可能的空格和下划线
                    subject_name = re.sub(r'[\s_]*term\s*\d+', '', str(full_name), flags=re.IGNORECASE).strip()
                    # 去掉末尾的下划线或空格
                    subject_name = re.sub(r'[_\s]+$', '', subject_name).strip()
                    # 如果科目名為空，跳過
                    if not subject_name or subject_name.lower() == 'nan':
                        continue
                    
                    # 處理 "--" 表示未修讀
                    if pd.isna(val) or str(val).strip() in ['--', 'NaN', 'nan', '']:
                        # 不添加，保持為空
                        pass
                    else:
                        try:
                            numeric_val = float(val)
                            if 0 <= numeric_val <= 100:
                                if subject_name not in subject_scores:
                                    subject_scores[subject_name] = []
                                subject_scores[subject_name].append(numeric_val)
                        except:
                            pass
                
                # 將同一科目的多個Term成績匯總
                for subject_name, scores in subject_scores.items():
                    if scores:
                        # 計算該科目的平均分（多個Term的平均）
                        record[f'{subject_name}'] = np.mean(scores)
                    else:
                        record[f'{subject_name}'] = None
                
                records.append(record)
            
            if records:
                result_df = pd.DataFrame(records)
                return result_df
            
            return pd.DataFrame()
            
        except Exception as e:
            print(f"載入 eClass 數據時出錯: {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()
    
    def _merge_term_scores(self, df: pd.DataFrame) -> pd.DataFrame:
        """將同一科目的多個Term成績合併為單一科目成績"""
        import re
        
        # 保留非科目列
        id_cols = ['English_Name', 'Student_ID', 'english_name', 'student_id']
        base_cols = [col for col in df.columns if col in id_cols]
        subject_cols = [col for col in df.columns if col not in id_cols]
        
        # 按科目分組（去掉Term部分）
        subject_groups = {}
        for col in subject_cols:
            # 提取科目名稱（去掉Term部分）
            # 例如 "English_Term1" -> "English", "Chinese Term2" -> "Chinese"
            subject_name = re.sub(r'[\s_]*term\s*\d+', '', str(col), flags=re.IGNORECASE).strip()
            # 去掉末尾的下划线或空格
            subject_name = re.sub(r'[_\s]+$', '', subject_name).strip()
            if not subject_name or subject_name.lower() == 'nan':
                continue
            
            if subject_name not in subject_groups:
                subject_groups[subject_name] = []
            subject_groups[subject_name].append(col)
        
        # 創建新數據框
        merged_df = df[base_cols].copy()
        
        # 對每個科目，計算多個Term的平均分
        for subject_name, term_cols in subject_groups.items():
            # 收集該科目的所有Term成績
            term_scores = df[term_cols].values
            
            # 計算每個學生的平均分（跨所有Term）
            avg_scores = []
            for row in term_scores:
                valid_scores = [float(s) for s in row if pd.notna(s) and str(s) != '--']
                if valid_scores:
                    avg_scores.append(np.mean(valid_scores))
                else:
                    avg_scores.append(None)
            
            merged_df[subject_name] = avg_scores
        
        return merged_df
    
    def extract_subject_features(self, eclass_df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """按科目提取特徵"""
        if eclass_df.empty:
            return {}
        
        # 標準化列名
        if 'English_Name' in eclass_df.columns and 'english_name' not in eclass_df.columns:
            eclass_df['english_name'] = eclass_df['English_Name']
        if 'English Name' in eclass_df.columns and 'english_name' not in eclass_df.columns:
            eclass_df['english_name'] = eclass_df['English Name']
        if 'student_id' not in eclass_df.columns:
            if 'Student_ID' in eclass_df.columns:
                eclass_df['student_id'] = eclass_df['Student_ID']
            elif 'english_name' in eclass_df.columns:
                eclass_df['student_id'] = eclass_df['english_name']
            else:
                eclass_df['student_id'] = eclass_df.iloc[:, 0]
        
        # 獲取所有科目列（排除 english_name、student_id 和 Average Score 相關列）
        exclude_cols = ['english_name', 'student_id', 'English_Name', 'English Name', 'Student_ID',
                       'Average_Score', 'Average Score', 'average_score', 'average score']
        subject_cols = [col for col in eclass_df.columns 
                        if col not in exclude_cols and 'average' not in col.lower()]
        
        subject_features = {}
        
        for subject_col in subject_cols:
            # 提取該科目的所有成績（可能有多個學期）
            subject_data = eclass_df[['english_name', 'student_id', subject_col]].copy()
            subject_data = subject_data[subject_data[subject_col].notna()]
            
            if len(subject_data) > 0:
                # 按學生分組，計算統計特徵
                features = []
                for english_name, group in subject_data.groupby('english_name'):
                    scores = group[subject_col].dropna().tolist()
                    if scores:
                        features.append({
                            'english_name': english_name,
                            'student_id': group['student_id'].iloc[0],
                            f'{subject_col}_mean': np.mean(scores),
                            f'{subject_col}_max': np.max(scores),
                            f'{subject_col}_min': np.min(scores),
                            f'{subject_col}_std': np.std(scores) if len(scores) > 1 else 0,
                            f'{subject_col}_count': len(scores)
                        })
                
                if features:
                    subject_features[subject_col] = pd.DataFrame(features)
        
        return subject_features
    
    def predict_by_subject(self, eclass_file: Path, model_path: Path) -> List[Dict]:
        """按科目進行預測"""
        # 載入詳細的 eClass 數據
        eclass_df = self.load_eclass_data_detailed(eclass_file)
        
        if eclass_df.empty:
            raise ValueError("無法從 eClass 數據中提取信息")
        
        # 標準化列名
        # 優先使用UserLogin作為學生ID
        if 'UserLogin' in eclass_df.columns:
            eclass_df['student_id'] = eclass_df['UserLogin']
        elif 'Student_ID' in eclass_df.columns:
            eclass_df['student_id'] = eclass_df['Student_ID']
        elif 'student_id' not in eclass_df.columns:
            # 使用第一列作為student_id
            first_col = eclass_df.columns[0]
            eclass_df['student_id'] = eclass_df[first_col]
        
        # 獲取English Name（用於顯示）
        if 'English_Name' in eclass_df.columns:
            eclass_df['english_name'] = eclass_df['English_Name']
        elif 'English Name' in eclass_df.columns:
            eclass_df['english_name'] = eclass_df['English Name']
        elif 'english_name' not in eclass_df.columns:
            # 如果沒有English Name，使用student_id作為顯示名稱
            eclass_df['english_name'] = eclass_df['student_id']
        
        # 載入整體模型（用於備用預測）
        try:
            overall_model = PredictionModel(target=self.target)
            overall_model.load_model(model_path)
        except:
            overall_model = None
        
        # 提取科目特徵（可選，目前不使用）
        # subject_features = self.extract_subject_features(eclass_df)
        
        # 為每個學生創建預測結果
        results = []
        
        for _, student_row in eclass_df.iterrows():
            english_name = student_row.get('english_name') or student_row.get('English_Name')
            student_id = student_row.get('student_id') or student_row.get('Student_ID') or english_name
            
            student_result = {
                'english_name': english_name,
                'student_id': student_id,
                'subjects': {}
            }
            
            # 對每個科目進行預測（科目已經按Term匯總過了）
            # 排除 Average Score 相關列
            exclude_cols = ['english_name', 'student_id', 'English_Name', 'Student_ID', 
                          'Average_Score', 'Average Score', 'average_score', 'average score']
            for subject_col in [col for col in eclass_df.columns 
                               if col not in exclude_cols]:
                # 獲取該科目的成績（已經是匯總後的平均分）
                subject_score = None
                if subject_col in student_row.index:
                    val = student_row[subject_col]
                    if pd.notna(val) and str(val) != '--':
                        try:
                            subject_score = float(val)
                            if not (0 <= subject_score <= 100):
                                subject_score = None
                        except:
                            subject_score = None
                
                # 如果有成績，進行預測
                if subject_score is not None:
                    avg_score = subject_score
                    
                    # 簡單的線性映射預測（可以改進為使用實際模型）
                    if self.target.lower() == 'hkdse':
                        # HKDSE: 基於平均成績映射到等級
                        if avg_score >= 90:
                            predicted = 5.0
                        elif avg_score >= 80:
                            predicted = 4.5
                        elif avg_score >= 70:
                            predicted = 4.0
                        elif avg_score >= 60:
                            predicted = 3.0
                        elif avg_score >= 50:
                            predicted = 2.0
                        else:
                            predicted = 1.0
                    else:  # IB
                        # IB: 基於平均成績映射到等級
                        if avg_score >= 90:
                            predicted = 7.0
                        elif avg_score >= 80:
                            predicted = 6.0
                        elif avg_score >= 70:
                            predicted = 5.0
                        elif avg_score >= 60:
                            predicted = 4.0
                        elif avg_score >= 50:
                            predicted = 3.0
                        else:
                            predicted = 2.0
                    
                    student_result['subjects'][subject_col] = {
                        'eclass_score': avg_score,
                        'predicted_score': predicted,
                        'has_data': True
                    }
                else:
                    # 未修讀該科目
                    student_result['subjects'][subject_col] = {
                        'eclass_score': None,
                        'predicted_score': None,
                        'has_data': False
                    }
            
            results.append(student_result)
        
        return results


def format_prediction_results(results: List[Dict], target: str) -> pd.DataFrame:
    """格式化預測結果為表格"""
    rows = []
    
    for result in results:
        english_name = result['english_name']
        base_row = {
            'English Name': english_name,
            'Student ID': result['student_id']
        }
        
        # 為每個科目添加列（排除 Average Score）
        for subject, pred_data in result['subjects'].items():
            # 跳過 Average Score 相關科目
            if subject.lower() in ['average_score', 'average score', 'average']:
                continue
                
            if pred_data['has_data']:
                if target.lower() == 'hkdse':
                    base_row[f'{subject} (eClass)'] = f"{pred_data['eclass_score']:.1f}"
                    base_row[f'{subject} (Predicted HKDSE)'] = f"{pred_data['predicted_score']:.1f}"
                else:
                    base_row[f'{subject} (eClass)'] = f"{pred_data['eclass_score']:.1f}"
                    base_row[f'{subject} (Predicted IB)'] = f"{pred_data['predicted_score']:.1f}"
            else:
                base_row[f'{subject}'] = '-- (未修讀)'
        
        rows.append(base_row)
    
    return pd.DataFrame(rows)


if __name__ == "__main__":
    # 測試
    predictor = SubjectBasedPredictor(target='hkdse')
    sample_file = Path('sample_files/sample_eclass_data.xlsx')
    model_path = Path('models/hkdse_model.pkl')
    
    if sample_file.exists():
        results = predictor.predict_by_subject(sample_file, model_path)
        df = format_prediction_results(results, 'hkdse')
        print(df)
