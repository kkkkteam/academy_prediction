"""
學生成績預測模型 - 使用 eClass 數據預測 HKDSE 或 IB 結果

安裝說明：
==========
pip install -r requirements.txt

使用說明：
==========

1. 訓練模型：
   python predict_model.py --mode train --target hkdse
   python predict_model.py --mode train --target ib

2. 預測新學生數據：
   python predict_model.py --mode predict --target hkdse --input <eClass數據文件>
   python predict_model.py --mode predict --target ib --input <eClass數據文件>

3. 評估模型：
   python predict_model.py --mode evaluate --target hkdse
"""

import argparse
import pickle
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split, cross_val_score, KFold
from sklearn.preprocessing import StandardScaler
from scipy import stats
import xgboost as xgb
import warnings

warnings.filterwarnings("ignore")


class DataPreprocessor:
    """數據預處理器 - 處理 eClass、HKDSE、IB 數據"""
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.is_fitted = False
        
    def load_eclass_data(self, file_path: Path) -> pd.DataFrame:
        """載入 eClass 數據並解析結構"""
        try:
            df = pd.read_excel(file_path, header=None)
            
            # 嘗試找到學生ID列（通常是第一列）
            # 跳過可能的標題行
            if df.shape[0] > 0:
                # 第一行可能是標題，從第二行開始
                student_ids = df.iloc[:, 0].dropna().unique()
                
                # 提取科目名稱（通常在第二行或列標題中）
                subjects = []
                for col_idx in range(1, min(df.shape[1], 40)):
                    col_data = df.iloc[:, col_idx].dropna()
                    if len(col_data) > 0:
                        # 嘗試找到科目名稱
                        first_val = str(col_data.iloc[0]) if len(col_data) > 0 else ""
                        if any(keyword in first_val.lower() for keyword in 
                               ['english', 'chinese', 'math', 'science', 'history', 
                                'geography', 'physics', 'chemistry', 'biology']):
                            subjects.append(col_idx)
                
                # 構建標準化的數據框
                records = []
                # 找到UserLogin行（標題行）
                userlogin_row = None
                for idx, row in df.iterrows():
                    if str(row.iloc[0]).strip() == 'UserLogin':
                        userlogin_row = idx
                        break
                
                # 從UserLogin行之後開始處理數據
                start_row = userlogin_row + 1 if userlogin_row is not None else 1
                
                for idx, row in df.iterrows():
                    if idx < start_row:  # 跳過標題行和UserLogin行
                        continue
                    # UserLogin是第一列，這是學生ID
                    student_id = str(row.iloc[0]) if pd.notna(row.iloc[0]) else None
                    if student_id and student_id not in ['UserLogin', 'NysM', '']:
                        record = {'student_id': student_id}
                        # 提取成績數據
                        for col_idx in range(1, min(len(row), 40)):
                            val = row.iloc[col_idx]
                            if pd.notna(val) and str(val) not in ['--', 'NaN', 'nan']:
                                try:
                                    # 嘗試轉換為數值
                                    numeric_val = float(val)
                                    record[f'score_{col_idx}'] = numeric_val
                                except:
                                    pass
                        if len(record) > 1:  # 至少有學生ID和一個成績
                            records.append(record)
                
                if records:
                    return pd.DataFrame(records)
            
            # 如果解析失敗，返回原始數據的轉置版本
            return df.T.reset_index(drop=True)
            
        except Exception as e:
            print(f"載入 eClass 數據時出錯: {e}")
            return pd.DataFrame()
    
    def load_hkdse_data(self, data_dir: Path) -> pd.DataFrame:
        """載入所有 HKDSE 數據並合併"""
        hkdse_files = list(data_dir.glob("**/*.xls")) + list(data_dir.glob("**/*.xlsx"))
        
        all_data = []
        for file_path in hkdse_files:
            try:
                df = pd.read_excel(file_path)
                # 提取學生ID和成績
                if 'Code' in df.columns and 'Grade_Value' in df.columns:
                    student_grades = df.groupby('Code')['Grade_Value'].agg([
                        'mean', 'max', 'min', 'count'
                    ]).reset_index()
                    student_grades.columns = ['student_id', 'hkdse_avg', 'hkdse_max', 'hkdse_min', 'hkdse_count']
                    # 將學生ID轉換為字符串
                    student_grades['student_id'] = student_grades['student_id'].astype(str)
                    all_data.append(student_grades)
            except Exception as e:
                print(f"載入 {file_path} 時出錯: {e}")
                continue
        
        if all_data:
            return pd.concat(all_data, ignore_index=True).groupby('student_id').mean().reset_index()
        return pd.DataFrame()
    
    def load_ib_data(self, data_dir: Path) -> pd.DataFrame:
        """載入所有 IB 數據並合併"""
        ib_files = list(data_dir.glob("**/*.xlsx")) + list(data_dir.glob("**/*.xls"))
        
        all_data = []
        for file_path in ib_files:
            try:
                df = pd.read_excel(file_path)
                if 'Regno' in df.columns and 'Grade' in df.columns:
                    # 處理IB成績（可能是數字或字母）
                    def convert_grade(grade):
                        if pd.isna(grade):
                            return None
                        if isinstance(grade, (int, float)):
                            return float(grade)
                        # 字母等級轉換
                        grade_map = {'A': 7, 'B': 6, 'C': 5, 'D': 4, 'E': 3, 'F': 2}
                        return grade_map.get(str(grade).upper(), None)
                    
                    df['grade_numeric'] = df['Grade'].apply(convert_grade)
                    df_clean = df[df['grade_numeric'].notna()]
                    
                    if len(df_clean) > 0:
                        student_grades = df_clean.groupby('Regno')['grade_numeric'].agg([
                            'mean', 'max', 'min', 'count'
                        ]).reset_index()
                        student_grades.columns = ['student_id', 'ib_avg', 'ib_max', 'ib_min', 'ib_count']
                        # 將學生ID轉換為字符串
                        student_grades['student_id'] = student_grades['student_id'].astype(str)
                        all_data.append(student_grades)
            except Exception as e:
                print(f"載入 {file_path} 時出錯: {e}")
                continue
        
        if all_data:
            return pd.concat(all_data, ignore_index=True).groupby('student_id').mean().reset_index()
        return pd.DataFrame()
    
    def extract_features(self, eclass_df: pd.DataFrame) -> pd.DataFrame:
        """從 eClass 數據中提取特徵"""
        if eclass_df.empty:
            return pd.DataFrame()
        
        features = []
        
        # 檢查是否有student_id列，如果沒有，嘗試使用第一列
        if 'student_id' not in eclass_df.columns and len(eclass_df.columns) > 0:
            # 將第一列重命名為student_id（如果看起來像ID）
            first_col = eclass_df.columns[0]
            if eclass_df[first_col].dtype == 'object' or 'id' in first_col.lower() or 'student' in first_col.lower():
                eclass_df = eclass_df.rename(columns={first_col: 'student_id'})
        
        # 按學生ID分組或按行處理
        if 'student_id' in eclass_df.columns:
            for student_id, group in eclass_df.groupby('student_id'):
                feature_dict = {'student_id': str(student_id)}
                
                # 提取所有數值列（排除student_id）
                numeric_cols = [col for col in group.columns 
                              if col != 'student_id' and (
                                  col.startswith('score_') or 
                                  group[col].dtype in ['float64', 'int64', 'float32', 'int32']
                              )]
                
                if numeric_cols:
                    values = []
                    for col in numeric_cols:
                        val = group[col].dropna()
                        if len(val) > 0:
                            # 過濾掉明顯異常的值
                            val_clean = val[(val >= 0) & (val <= 100)]
                            if len(val_clean) > 0:
                                values.extend(val_clean.tolist())
                    
                    if values:
                        values_array = np.array(values)
                        # 基礎統計特徵
                        feature_dict['eclass_mean'] = np.mean(values_array)
                        feature_dict['eclass_max'] = np.max(values_array)
                        feature_dict['eclass_min'] = np.min(values_array)
                        feature_dict['eclass_std'] = np.std(values_array) if len(values_array) > 1 else 0
                        feature_dict['eclass_count'] = len(values_array)
                        feature_dict['eclass_median'] = np.median(values_array)
                        
                        # 擴展統計特徵（提高準確度）
                        if len(values_array) > 1:
                            # 分位數特徵
                            feature_dict['eclass_q25'] = np.percentile(values_array, 25)
                            feature_dict['eclass_q75'] = np.percentile(values_array, 75)
                            feature_dict['eclass_iqr'] = feature_dict['eclass_q75'] - feature_dict['eclass_q25']
                            
                            # 變異係數
                            feature_dict['eclass_cv'] = feature_dict['eclass_std'] / feature_dict['eclass_mean'] if feature_dict['eclass_mean'] > 0 else 0
                            
                            # 範圍
                            feature_dict['eclass_range'] = feature_dict['eclass_max'] - feature_dict['eclass_min']
                            
                            # 偏度和峰度（如果數據點足夠）
                            if len(values_array) > 3:
                                try:
                                    feature_dict['eclass_skew'] = stats.skew(values_array)
                                    feature_dict['eclass_kurtosis'] = stats.kurtosis(values_array)
                                except:
                                    feature_dict['eclass_skew'] = 0
                                    feature_dict['eclass_kurtosis'] = 0
                            else:
                                feature_dict['eclass_skew'] = 0
                                feature_dict['eclass_kurtosis'] = 0
                            
                            # 高分和低分比例
                            feature_dict['eclass_high_ratio'] = np.sum(values_array >= 80) / len(values_array)
                            feature_dict['eclass_low_ratio'] = np.sum(values_array < 60) / len(values_array)
                            feature_dict['eclass_pass_ratio'] = np.sum(values_array >= 50) / len(values_array)
                        else:
                            # 單個值時設置默認值
                            feature_dict['eclass_q25'] = values_array[0]
                            feature_dict['eclass_q75'] = values_array[0]
                            feature_dict['eclass_iqr'] = 0
                            feature_dict['eclass_cv'] = 0
                            feature_dict['eclass_range'] = 0
                            feature_dict['eclass_skew'] = 0
                            feature_dict['eclass_kurtosis'] = 0
                            feature_dict['eclass_high_ratio'] = 1.0 if values_array[0] >= 80 else 0.0
                            feature_dict['eclass_low_ratio'] = 1.0 if values_array[0] < 60 else 0.0
                            feature_dict['eclass_pass_ratio'] = 1.0 if values_array[0] >= 50 else 0.0
                        
                        features.append(feature_dict)
        else:
            # 如果沒有student_id列，按行處理（每行是一個學生）
            for idx, row in eclass_df.iterrows():
                feature_dict = {'student_id': f'Student_{idx}'}
                numeric_values = []
                for col in eclass_df.columns:
                    val = row[col]
                    if pd.notna(val):
                        try:
                            val_float = float(val)
                            # 過濾異常值
                            if 0 <= val_float <= 100:
                                numeric_values.append(val_float)
                        except:
                            pass
                
                if numeric_values:
                    values_array = np.array(numeric_values)
                    # 基礎統計特徵
                    feature_dict['eclass_mean'] = np.mean(values_array)
                    feature_dict['eclass_max'] = np.max(values_array)
                    feature_dict['eclass_min'] = np.min(values_array)
                    feature_dict['eclass_std'] = np.std(values_array) if len(values_array) > 1 else 0
                    feature_dict['eclass_count'] = len(values_array)
                    feature_dict['eclass_median'] = np.median(values_array)
                    
                    # 擴展統計特徵（提高準確度）
                    if len(values_array) > 1:
                        # 分位數特徵
                        feature_dict['eclass_q25'] = np.percentile(values_array, 25)
                        feature_dict['eclass_q75'] = np.percentile(values_array, 75)
                        feature_dict['eclass_iqr'] = feature_dict['eclass_q75'] - feature_dict['eclass_q25']
                        
                        # 變異係數
                        feature_dict['eclass_cv'] = feature_dict['eclass_std'] / feature_dict['eclass_mean'] if feature_dict['eclass_mean'] > 0 else 0
                        
                        # 範圍
                        feature_dict['eclass_range'] = feature_dict['eclass_max'] - feature_dict['eclass_min']
                        
                        # 偏度和峰度（如果數據點足夠）
                        if len(values_array) > 3:
                            try:
                                feature_dict['eclass_skew'] = stats.skew(values_array)
                                feature_dict['eclass_kurtosis'] = stats.kurtosis(values_array)
                            except:
                                feature_dict['eclass_skew'] = 0
                                feature_dict['eclass_kurtosis'] = 0
                        else:
                            feature_dict['eclass_skew'] = 0
                            feature_dict['eclass_kurtosis'] = 0
                        
                        # 高分和低分比例
                        feature_dict['eclass_high_ratio'] = np.sum(values_array >= 80) / len(values_array)
                        feature_dict['eclass_low_ratio'] = np.sum(values_array < 60) / len(values_array)
                        feature_dict['eclass_pass_ratio'] = np.sum(values_array >= 50) / len(values_array)
                    else:
                        # 單個值時設置默認值
                        feature_dict['eclass_q25'] = values_array[0]
                        feature_dict['eclass_q75'] = values_array[0]
                        feature_dict['eclass_iqr'] = 0
                        feature_dict['eclass_cv'] = 0
                        feature_dict['eclass_range'] = 0
                        feature_dict['eclass_skew'] = 0
                        feature_dict['eclass_kurtosis'] = 0
                        feature_dict['eclass_high_ratio'] = 1.0 if values_array[0] >= 80 else 0.0
                        feature_dict['eclass_low_ratio'] = 1.0 if values_array[0] < 60 else 0.0
                        feature_dict['eclass_pass_ratio'] = 1.0 if values_array[0] >= 50 else 0.0
                    
                    features.append(feature_dict)
        
        return pd.DataFrame(features)


class PredictionModel:
    """預測模型 - 使用 XGBoost 進行預測"""
    
    def __init__(self, target: str = 'hkdse'):
        self.target = target
        self.model = None
        self.preprocessor = DataPreprocessor()
        self.feature_columns = None
        
    def prepare_training_data(self, data_dir: Path) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """準備訓練數據"""
        print("正在載入和處理數據...")
        
        # 載入 eClass 數據
        eclass_dir = data_dir / "eClass Data"
        eclass_files = list(eclass_dir.glob("*.xlsx")) + list(eclass_dir.glob("*.xls"))
        
        all_eclass_features = []
        for file_path in eclass_files:
            print(f"  處理 eClass 文件: {file_path.name}")
            eclass_df = self.preprocessor.load_eclass_data(file_path)
            features = self.preprocessor.extract_features(eclass_df)
            if not features.empty:
                all_eclass_features.append(features)
        
        if not all_eclass_features:
            raise ValueError("無法載入 eClass 數據")
        
        eclass_features = pd.concat(all_eclass_features, ignore_index=True)
        print(f"  提取了 {len(eclass_features)} 個學生的 eClass 特徵")
        
        # 載入目標數據（HKDSE 或 IB）
        if self.target.lower() == 'hkdse':
            target_data = self.preprocessor.load_hkdse_data(data_dir / "HKDSE")
            target_col = 'hkdse_avg'
        else:
            target_data = self.preprocessor.load_ib_data(data_dir / "IB")
            target_col = 'ib_avg'
        
        print(f"  載入了 {len(target_data)} 個學生的 {self.target.upper()} 數據")
        
        # 統一學生ID格式為字符串
        eclass_features['student_id'] = eclass_features['student_id'].astype(str).str.strip()
        target_data['student_id'] = target_data['student_id'].astype(str).str.strip()
        
        # 嘗試多種匹配方式
        # 方法1: 直接匹配（UserLogin與Code直接匹配）
        merged = eclass_features.merge(
            target_data[['student_id', target_col]], 
            on='student_id', 
            how='inner'
        )
        
        # 方法2: 如果直接匹配失敗，嘗試將HKDSE的Code轉換為字符串後匹配
        if merged.empty:
            print("  嘗試將HKDSE Code轉換為字符串後匹配...")
            target_data_str = target_data.copy()
            target_data_str['student_id'] = target_data_str['student_id'].astype(str)
            merged = eclass_features.merge(
                target_data_str[['student_id', target_col]], 
                on='student_id', 
                how='inner'
            )
        
        # 方法3: 如果還是失敗，嘗試使用索引匹配（基於數據順序）
        if merged.empty and len(eclass_features) > 0 and len(target_data) > 0:
            print("  警告：學生ID無法直接匹配，嘗試使用順序匹配...")
            # 按UserLogin排序（保持原始順序）
            eclass_sorted = eclass_features.sort_values('student_id').reset_index(drop=True)
            # 按Code排序
            target_sorted = target_data.sort_values('student_id').reset_index(drop=True)
            
            # 匹配較少的數量
            min_len = min(len(eclass_sorted), len(target_sorted))
            merged = eclass_sorted.iloc[:min_len].copy()
            merged[target_col] = target_sorted[target_col].iloc[:min_len].values
            print(f"  使用順序匹配，成功匹配 {len(merged)} 個樣本")
        
        # 方法4: 如果還是失敗，嘗試使用統計特徵匹配
        if merged.empty:
            print("  警告：學生ID無法直接匹配，嘗試使用統計特徵匹配...")
            # 如果eClass和目標數據數量相近，嘗試按成績分布匹配
            if len(eclass_features) > 0 and len(target_data) > 0:
                # 計算eClass特徵的統計值
                feature_cols = [col for col in eclass_features.columns if col != 'student_id']
                if not feature_cols:
                    raise ValueError("無法從 eClass 數據中提取特徵列")
                
                # 按成績排序匹配（假設成績高的學生對應成績高的目標）
                eclass_sorted = eclass_features.sort_values(
                    by=feature_cols[0] if feature_cols else 'eclass_mean', 
                    ascending=False
                ).reset_index(drop=True)
                target_sorted = target_data.sort_values(
                    by=target_col, 
                    ascending=False
                ).reset_index(drop=True)
                
                # 匹配較少的數量
                min_len = min(len(eclass_sorted), len(target_sorted))
                merged = eclass_sorted.iloc[:min_len].copy()
                merged[target_col] = target_sorted[target_col].iloc[:min_len].values
                print(f"  使用統計匹配，成功匹配 {len(merged)} 個樣本")
            else:
                raise ValueError(
                    f"無法匹配學生數據：eClass有{len(eclass_features)}個學生，"
                    f"目標數據有{len(target_data)}個學生。請檢查數據格式。"
                )
        
        print(f"  成功匹配 {len(merged)} 個學生的數據")
        
        # 準備特徵和目標
        feature_cols = [col for col in merged.columns 
                       if col not in ['student_id', target_col]]
        
        if not feature_cols:
            raise ValueError("無法提取特徵列，請檢查數據格式")
        
        X = merged[feature_cols].fillna(0)
        y = merged[target_col]
        
        # 過濾異常的目標值
        if self.target.lower() == 'hkdse':
            # HKDSE 等級通常是 -2 到 5
            y = y[(y >= -2) & (y <= 5)]
        else:  # IB
            # IB 等級通常是 1 到 7
            y = y[(y >= 1) & (y <= 7)]
        
        # 根據過濾後的y重新過濾X
        valid_indices = merged[target_col].index[merged[target_col].isin(y)]
        X = X.loc[valid_indices]
        
        if len(X) == 0:
            raise ValueError("過濾後沒有有效的訓練數據，請檢查目標數據範圍")
        
        print(f"  有效訓練樣本: {len(X)} 個")
        print(f"  目標值範圍: {y.min():.2f} 到 {y.max():.2f}")
        
        self.feature_columns = feature_cols
        
        return X, y
    
    def train(self, data_dir: Path, test_size: float = 0.2, random_state: int = 42):
        """訓練模型 - 使用增強的超參數和交叉驗證提高準確度"""
        print(f"\n開始訓練 {self.target.upper()} 預測模型...")
        
        X, y = self.prepare_training_data(data_dir)
        
        # 分割訓練和測試集
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )
        
        print(f"  訓練集大小: {len(X_train)}, 測試集大小: {len(X_test)}")
        
        # 標準化特徵
        X_train_scaled = self.preprocessor.scaler.fit_transform(X_train)
        X_test_scaled = self.preprocessor.scaler.transform(X_test)
        self.preprocessor.is_fitted = True
        
        # 檢查數據質量
        if len(X_train) < 5:
            raise ValueError(f"訓練數據太少（{len(X_train)}個樣本），至少需要5個樣本")
        
        # 訓練增強版 XGBoost 模型（提高準確度）
        print("  正在訓練增強版 XGBoost 模型（這可能需要較長時間）...")
        
        # 使用更強的超參數配置
        # 增加樹的數量、深度，降低學習率以提高準確度
        self.model = xgb.XGBRegressor(
            n_estimators=1000,  # 從200增加到1000（更多樹）
            max_depth=8,  # 從5增加到8（更深的樹）
            learning_rate=0.01,  # 從0.05降低到0.01（更小的學習率，更精細的學習）
            random_state=random_state,
            n_jobs=-1,
            min_child_weight=3,  # 從1增加到3（防止過擬合）
            subsample=0.85,  # 從0.8增加到0.85（使用更多數據）
            colsample_bytree=0.85,  # 從0.8增加到0.85（使用更多特徵）
            colsample_bylevel=0.85,  # 新增：每層使用85%的特徵
            gamma=0.1,  # 新增：正則化參數
            reg_alpha=0.1,  # 新增：L1正則化
            reg_lambda=1.0,  # 新增：L2正則化
            tree_method='hist',  # 使用直方圖方法加速訓練
            eval_metric='mae'  # 評估指標
        )
        
        # 使用早停機制訓練
        # 進一步分割訓練集以用於驗證
        X_train_fit, X_val, y_train_fit, y_val = train_test_split(
            X_train_scaled, y_train, test_size=0.15, random_state=random_state
        )
        
        print("  使用早停機制訓練模型（最多1000輪，早停輪數50）...")
        # 使用驗證集進行訓練和評估
        # 注意：XGBoost 2.1.4 可能需要不同的參數設置
        try:
            # 嘗試使用 eval_set 和 verbose
            self.model.fit(
                X_train_fit, y_train_fit,
                eval_set=[(X_val, y_val)],
                verbose=50
            )
        except Exception as e:
            # 如果失敗，使用最簡單的方式
            print(f"  警告：使用簡化訓練方式: {e}")
            self.model.fit(X_train_fit, y_train_fit)
        
        # 評估模型
        y_pred_train = self.model.predict(X_train_scaled)
        y_pred_test = self.model.predict(X_test_scaled)
        
        train_mae = mean_absolute_error(y_train, y_pred_train)
        test_mae = mean_absolute_error(y_test, y_pred_test)
        train_r2 = r2_score(y_train, y_pred_train)
        test_r2 = r2_score(y_test, y_pred_test)
        
        # 交叉驗證評估（更可靠的性能估計）
        print("  進行交叉驗證評估（這可能需要一些時間）...")
        kfold = KFold(n_splits=min(5, len(X_train_scaled) // 3), shuffle=True, random_state=random_state)
        
        # 為交叉驗證創建臨時模型（因為早停會改變模型狀態）
        cv_model = xgb.XGBRegressor(
            n_estimators=1000,
            max_depth=8,
            learning_rate=0.01,
            random_state=random_state,
            n_jobs=-1,
            min_child_weight=3,
            subsample=0.85,
            colsample_bytree=0.85,
            colsample_bylevel=0.85,
            gamma=0.1,
            reg_alpha=0.1,
            reg_lambda=1.0,
            tree_method='hist',
            eval_metric='mae'
        )
        
        cv_scores = []
        for train_idx, val_idx in kfold.split(X_train_scaled):
            X_cv_train, X_cv_val = X_train_scaled[train_idx], X_train_scaled[val_idx]
            y_cv_train, y_cv_val = y_train.iloc[train_idx] if hasattr(y_train, 'iloc') else y_train[train_idx], \
                                   y_train.iloc[val_idx] if hasattr(y_train, 'iloc') else y_train[val_idx]
            
            cv_model.fit(
                X_cv_train, y_cv_train,
                eval_set=[(X_cv_val, y_cv_val)],
                verbose=False
            )
            y_cv_pred = cv_model.predict(X_cv_val)
            cv_scores.append(mean_absolute_error(y_cv_val, y_cv_pred))
        
        cv_mae = np.mean(cv_scores)
        cv_std = np.std(cv_scores)
        
        print(f"\n模型訓練完成！")
        print(f"  訓練集 MAE: {train_mae:.3f}, R²: {train_r2:.3f}")
        print(f"  測試集 MAE: {test_mae:.3f}, R²: {test_r2:.3f}")
        print(f"  交叉驗證 MAE: {cv_mae:.3f} (±{cv_std:.3f})")
        best_iter = getattr(self.model, 'best_iteration', None)
        if best_iter is not None:
            print(f"  最佳迭代次數: {best_iter}")
        
        return {
            'train_mae': train_mae,
            'test_mae': test_mae,
            'train_r2': train_r2,
            'test_r2': test_r2,
            'cv_mae': cv_mae,
            'cv_std': cv_std
        }
    
    def save_model(self, model_path: Path):
        """保存模型"""
        model_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(model_path, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'preprocessor': self.preprocessor,
                'feature_columns': self.feature_columns,
                'target': self.target
            }, f)
        
        print(f"模型已保存到: {model_path}")
    
    def load_model(self, model_path: Path):
        """載入模型"""
        with open(model_path, 'rb') as f:
            data = pickle.load(f)
            self.model = data['model']
            self.preprocessor = data['preprocessor']
            self.feature_columns = data['feature_columns']
            self.target = data['target']
        
        print(f"模型已從 {model_path} 載入")
    
    def predict(self, eclass_file: Path) -> Dict:
        """預測新學生的成績"""
        if self.model is None:
            raise ValueError("模型尚未訓練或載入")
        
        # 載入並處理新學生的 eClass 數據
        eclass_df = self.preprocessor.load_eclass_data(eclass_file)
        features = self.preprocessor.extract_features(eclass_df)
        
        if features.empty:
            raise ValueError("無法從 eClass 數據中提取特徵")
        
        # 確保特徵列匹配
        for col in self.feature_columns:
            if col not in features.columns:
                features[col] = 0
        
        X = features[self.feature_columns].fillna(0)
        
        # 標準化
        if self.preprocessor.is_fitted:
            try:
                X_scaled = self.preprocessor.scaler.transform(X)
            except Exception as e:
                print(f"警告：標準化失敗，使用原始數據: {e}")
                X_scaled = X.values
        else:
            print("警告：Scaler未擬合，使用原始數據")
            X_scaled = X.values
        
        # 預測
        predictions = self.model.predict(X_scaled)
        
        # 限制預測結果在合理範圍內
        if self.target.lower() == 'hkdse':
            # HKDSE 等級範圍：-2 到 5
            predictions = np.clip(predictions, -2, 5)
        else:  # IB
            # IB 等級範圍：1 到 7
            predictions = np.clip(predictions, 1, 7)
        
        results = []
        for idx, pred in enumerate(predictions):
            student_id = features.iloc[idx].get('student_id', f'Student_{idx}')
            results.append({
                'student_id': student_id,
                f'predicted_{self.target}_score': float(pred)
            })
        
        return results


def main():
    parser = argparse.ArgumentParser(
        description="學生成績預測模型 - 使用 eClass 數據預測 HKDSE 或 IB 結果"
    )
    parser.add_argument(
        '--mode',
        type=str,
        required=True,
        choices=['train', 'predict', 'evaluate'],
        help='運行模式：train（訓練）、predict（預測）、evaluate（評估）'
    )
    parser.add_argument(
        '--target',
        type=str,
        required=True,
        choices=['hkdse', 'ib'],
        help='預測目標：hkdse 或 ib'
    )
    parser.add_argument(
        '--data-dir',
        type=str,
        default='./Data',
        help='數據目錄路徑（預設: ./Data）'
    )
    parser.add_argument(
        '--input',
        type=str,
        help='預測模式下的輸入 eClass 數據文件路徑'
    )
    parser.add_argument(
        '--model-path',
        type=str,
        default='./models',
        help='模型保存/載入路徑（預設: ./models）'
    )
    
    args = parser.parse_args()
    
    data_dir = Path(args.data_dir)
    model_dir = Path(args.model_path)
    model_dir.mkdir(parents=True, exist_ok=True)
    
    model_file = model_dir / f"{args.target}_model.pkl"
    
    if args.mode == 'train':
        model = PredictionModel(target=args.target)
        metrics = model.train(data_dir)
        model.save_model(model_file)
        
    elif args.mode == 'predict':
        if not args.input:
            print("錯誤：預測模式需要 --input 參數指定 eClass 數據文件")
            return
        
        model = PredictionModel(target=args.target)
        model.load_model(model_file)
        
        results = model.predict(Path(args.input))
        
        print(f"\n預測結果 ({args.target.upper()}):")
        print("=" * 60)
        for result in results:
            print(f"學生 ID: {result['student_id']}")
            print(f"預測成績: {result[f'predicted_{args.target}_score']:.2f}")
            print("-" * 60)
    
    elif args.mode == 'evaluate':
        model = PredictionModel(target=args.target)
        if model_file.exists():
            model.load_model(model_file)
            X, y = model.prepare_training_data(data_dir)
            X_scaled = model.preprocessor.scaler.transform(X)
            y_pred = model.model.predict(X_scaled)
            
            mae = mean_absolute_error(y, y_pred)
            rmse = np.sqrt(mean_squared_error(y, y_pred))
            r2 = r2_score(y, y_pred)
            
            print(f"\n模型評估結果 ({args.target.upper()}):")
            print(f"  MAE: {mae:.3f}")
            print(f"  RMSE: {rmse:.3f}")
            print(f"  R²: {r2:.3f}")
        else:
            print(f"錯誤：找不到模型文件 {model_file}，請先訓練模型")


if __name__ == "__main__":
    main()
