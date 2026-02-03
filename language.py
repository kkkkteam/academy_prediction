"""
多語言支持 - 中文和英文界面
"""

LANGUAGES = {
    'zh': {
        'title': '📊 學生成績預測系統',
        'description': '這個系統可以根據學生的 eClass 數據預測他們的 **HKDSE** 或 **IB** 考試結果。',
        'usage_steps': '使用步驟：',
        'step1': '選擇預測目標（HKDSE 或 IB）',
        'step2': '**下載示例文件**（確保數據格式正確）',
        'step3': '上傳學生的 eClass 數據文件（Excel 格式）',
        'step4': '點擊「開始預測」按鈕',
        'step5': '查看預測結果（**按科目分別顯示**）',
        'data_format': '數據格式要求：',
        'data_col1': '**第一列**：English Name（英文姓名，用作主鍵）',
        'data_col2': '**第二列**：Student ID（可選）',
        'data_col3': '**後續列**：各科目成績（數值，0-100）',
        'data_term_note': '  - 可以包含多個學期（Term），例如：`English Term1`, `English Term2`, `English Term3`',
        'data_term_merge': '  - **系統會自動將同一科目的多個Term成績合併為該科目的平均分**',
        'data_no_subject': '**未修讀科目**：使用 "--" 標記',
        'data_formats': '支持格式：`.xlsx`, `.xls`, `.csv`',
        'data_sample': '示例文件包含10個學生的示例數據',
        'important_note': '重要說明：',
        'term_meaning': '**Term 是學期的意思**：例如 `English Term1` = English 科目的第一學期',
        'predict_by_subject': '**預測結果按科目顯示**：系統會將同一科目的多個Term成績合併後進行預測',
        'grade_labels': '**年級標識**：S3（三年級）| S4（四年級）| S5（五年級）| S6（六年級）| MOCK（模擬公開試）',
        
        'sidebar_title': '模型狀態',
        'model_ready': '✓ {target} 模型已就緒',
        'model_not_ready': '✗ {target} 模型未訓練',
        'train_instruction': '請先運行 `python train_model.py --target {target}` 訓練模型',
        'train_guide': '訓練模型',
        'view_train_guide': '查看訓練說明',
        
        'prediction_settings': '預測設置',
        'select_target': '選擇預測目標：',
        'select_target_help': '選擇要預測的考試類型',
        'upload_data': '上傳數據',
        'download_sample': '📥 下載示例文件',
        'download_sample_help': '下載示例文件以了解正確的數據格式',
        'sample_tip': '💡 提示：下載示例文件以確保數據格式正確',
        'select_file': '選擇 eClass 數據文件',
        'select_file_help': '上傳學生的 eClass 成績數據文件。第一列應為學生ID，後續列為各科目成績（數值）',
        
        'prediction_results': '預測結果',
        'file_uploaded': '📄 已上傳文件：{filename}',
        'start_prediction': '🚀 開始預測',
        'processing': '正在處理數據並進行預測...',
        'prediction_complete': '✅ 預測完成！',
        'overview': '📊 預測結果總覽',
        'details': '📚 各學生科目預測詳情',
        'student': '👤 {name}',
        'student_id_label': '學生 ID: {id}',
        'subjects_with_data': '已修讀科目預測：',
        'subjects_without_data': '未修讀科目：',
        'not_taken_subjects': '以下科目標記為 \'--\'（未修讀）：{subjects}',
        'download_results': '📥 下載預測結果 (CSV)',
        
        'subject': '科目',
        'eclass_avg': 'eClass 平均分',
        'predicted_hkdse': '預測 HKDSE',
        'predicted_ib': '預測 IB',
        'predicted_grade': '預估等級',
        
        'hkdse_grades': {
            '5**': '5** (最高等級)',
            '5*': '5*',
            '5': '5',
            '4': '4',
            '3': '3',
            '2': '2',
            '1': '1 或 U (不合格)'
        },
        'ib_grades': {
            '7': '7 (最高等級)',
            '6': '6',
            '5': '5',
            '4': '4',
            '3': '3 或以下'
        },
        
        'error_model_not_trained': '⚠️ {target} 模型尚未訓練，請先訓練模型。',
        'error_train_command': '運行命令：`python train_model.py --target {target_lower}`',
        'error_no_file': '👆 請在左側上傳 eClass 數據文件開始預測',
        'error_prediction': '❌ 預測過程中發生錯誤：{error}',
        
        'footer': '學生成績預測系統 v1.0 | 基於機器學習模型'
    },
    'en': {
        'title': '📊 Student Performance Prediction System',
        'description': 'This system can predict students\' **HKDSE** or **IB** examination results based on their eClass data.',
        'usage_steps': 'Usage Steps:',
        'step1': 'Select prediction target (HKDSE or IB)',
        'step2': '**Download sample file** (to ensure correct data format)',
        'step3': 'Upload student eClass data file (Excel format)',
        'step4': 'Click "Start Prediction" button',
        'step5': 'View prediction results (**displayed by subject**)',
        'data_format': 'Data Format Requirements:',
        'data_col1': '**First Column**: English Name (used as primary key)',
        'data_col2': '**Second Column**: Student ID (optional)',
        'data_col3': '**Subsequent Columns**: Subject scores (numeric, 0-100)',
        'data_term_note': '  - Can include multiple terms, e.g., `English Term1`, `English Term2`, `English Term3`',
        'data_term_merge': '  - **System will automatically merge multiple Term scores for the same subject into average**',
        'data_no_subject': '**Subjects not taken**: Use "--" mark',
        'data_formats': 'Supported formats: `.xlsx`, `.xls`, `.csv`',
        'data_sample': 'Sample file contains example data for 10 students',
        'important_note': 'Important Notes:',
        'term_meaning': '**Term means semester**: e.g., `English Term1` = First semester of English subject',
        'predict_by_subject': '**Results displayed by subject**: System will merge multiple Term scores before prediction',
        'grade_labels': '**Grade Labels**: S3 (Form 3) | S4 (Form 4) | S5 (Form 5) | S6 (Form 6) | MOCK (Mock Exam)',
        
        'sidebar_title': 'Model Status',
        'model_ready': '✓ {target} model ready',
        'model_not_ready': '✗ {target} model not trained',
        'train_instruction': 'Please run `python train_model.py --target {target}` to train the model first',
        'train_guide': 'Train Model',
        'view_train_guide': 'View Training Guide',
        
        'prediction_settings': 'Prediction Settings',
        'select_target': 'Select Prediction Target:',
        'select_target_help': 'Select the examination type to predict',
        'upload_data': 'Upload Data',
        'download_sample': '📥 Download Sample File',
        'download_sample_help': 'Download sample file to understand the correct data format',
        'sample_tip': '💡 Tip: Download sample file to ensure correct data format',
        'select_file': 'Select eClass Data File',
        'select_file_help': 'Upload student eClass score data file. First column should be student ID, subsequent columns are subject scores (numeric)',
        
        'prediction_results': 'Prediction Results',
        'file_uploaded': '📄 Uploaded file: {filename}',
        'start_prediction': '🚀 Start Prediction',
        'processing': 'Processing data and making predictions...',
        'prediction_complete': '✅ Prediction Complete!',
        'overview': '📊 Prediction Results Overview',
        'details': '📚 Subject Prediction Details by Student',
        'student': '👤 {name}',
        'student_id_label': 'Student ID: {id}',
        'subjects_with_data': 'Subjects Taken - Predictions:',
        'subjects_without_data': 'Subjects Not Taken:',
        'not_taken_subjects': 'The following subjects are marked as \'--\' (not taken): {subjects}',
        'download_results': '📥 Download Prediction Results (CSV)',
        
        'subject': 'Subject',
        'eclass_avg': 'eClass Average',
        'predicted_hkdse': 'Predicted HKDSE',
        'predicted_ib': 'Predicted IB',
        'predicted_grade': 'Predicted Grade',
        
        'hkdse_grades': {
            '5**': '5** (Highest)',
            '5*': '5*',
            '5': '5',
            '4': '4',
            '3': '3',
            '2': '2',
            '1': '1 or U (Fail)'
        },
        'ib_grades': {
            '7': '7 (Highest)',
            '6': '6',
            '5': '5',
            '4': '4',
            '3': '3 or below'
        },
        
        'error_model_not_trained': '⚠️ {target} model not trained yet. Please train the model first.',
        'error_train_command': 'Run command: `python train_model.py --target {target_lower}`',
        'error_no_file': '👆 Please upload eClass data file on the left to start prediction',
        'error_prediction': '❌ Error occurred during prediction: {error}',
        
        'footer': 'Student Performance Prediction System v1.0 | Based on Machine Learning Model'
    }
}


def get_text(lang: str, key: str, **kwargs) -> str:
    """獲取翻譯文本"""
    if lang not in LANGUAGES:
        lang = 'zh'  # 默認中文
    
    text = LANGUAGES[lang].get(key, key)
    
    # 替換參數
    if kwargs:
        try:
            text = text.format(**kwargs)
        except:
            pass
    
    return text
