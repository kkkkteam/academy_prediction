"""
學生成績預測 Web UI - Streamlit 應用

使用方法：
  streamlit run app.py

功能：
  - 上傳 eClass 數據文件
  - 選擇預測目標（HKDSE 或 IB）
  - 查看預測結果
"""

import streamlit as st
import pandas as pd
from pathlib import Path
import tempfile
import os
from predict_model import PredictionModel
from predict_by_subject import SubjectBasedPredictor, format_prediction_results
from language import get_text
import sys
import warnings
import atexit

# 抑制 Streamlit 關閉時的無害警告
warnings.filterwarnings("ignore", category=RuntimeWarning)

# 處理關閉時的 Event loop 錯誤
def suppress_event_loop_error():
    """抑制關閉時的 Event loop 錯誤"""
    import sys
    
    def exception_handler(exc_type, exc_value, exc_traceback):
        if exc_type is RuntimeError and "Event loop is closed" in str(exc_value):
            # 忽略關閉時的無害錯誤
            return
        # 其他錯誤正常處理
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
    
    # 設置異常處理器
    sys.excepthook = exception_handler

# 註冊清理函數
atexit.register(suppress_event_loop_error)

# 初始化session state
if 'language' not in st.session_state:
    st.session_state.language = 'zh'

# 設置頁面配置
st.set_page_config(
    page_title="學生成績預測系統 / Student Performance Prediction",
    page_icon="📊",
    layout="wide"
)

model_dir = Path("./models")
hkdse_model_path = model_dir / "hkdse_model.pkl"
ib_model_path = model_dir / "ib_model.pkl"


def _prediction_page():
    """學生成績預測主頁"""
    lang = st.session_state.language
    # 語言切換固定右上角
    _c1, _c2 = st.columns([5, 1])
    with _c2:
        lang_choice = st.selectbox(
            "🌐 Language / 語言",
            options=['zh', 'en'],
            index=0 if lang == 'zh' else 1,
            format_func=lambda x: '中文' if x == 'zh' else 'English'
        )
        if lang_choice != lang:
            st.session_state.language = lang_choice
            st.rerun()
    st.title(get_text(lang, 'title'))
    st.markdown("---")
    st.markdown(f"""
{get_text(lang, 'description')}

### {get_text(lang, 'usage_steps')}
1. {get_text(lang, 'step1')}
2. {get_text(lang, 'step2')}
3. {get_text(lang, 'step3')}
4. {get_text(lang, 'step4')}
5. {get_text(lang, 'step5')}

### {get_text(lang, 'data_format')}
- {get_text(lang, 'data_col1')}
- {get_text(lang, 'data_col2')}
- {get_text(lang, 'data_col3')}
{get_text(lang, 'data_term_note')}
{get_text(lang, 'data_term_merge')}
- {get_text(lang, 'data_no_subject')}
- {get_text(lang, 'data_formats')}
- {get_text(lang, 'data_sample')}

### {get_text(lang, 'important_note')}
- {get_text(lang, 'term_meaning')}
- {get_text(lang, 'predict_by_subject')}
- {get_text(lang, 'grade_labels')}
""")
    st.sidebar.title(get_text(lang, 'sidebar_title'))
    st.sidebar.markdown("---")
    hkdse_available = hkdse_model_path.exists()
    ib_available = ib_model_path.exists()
    if hkdse_available:
        st.sidebar.success(get_text(lang, 'model_ready', target='HKDSE'))
    else:
        st.sidebar.error(get_text(lang, 'model_not_ready', target='HKDSE'))
        st.sidebar.info(get_text(lang, 'train_instruction', target='hkdse'))
    if ib_available:
        st.sidebar.success(get_text(lang, 'model_ready', target='IB'))
    else:
        st.sidebar.error(get_text(lang, 'model_not_ready', target='IB'))
        st.sidebar.info(get_text(lang, 'train_instruction', target='ib'))
    st.sidebar.markdown("---")
    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader(get_text(lang, 'prediction_settings'))
        target = st.radio(
            get_text(lang, 'select_target'),
            ["HKDSE", "IB"],
            help=get_text(lang, 'select_target_help')
        )
        target_lower = target.lower()
        model_path = model_dir / f"{target_lower}_model.pkl"
        model_available = model_path.exists()
        if not model_available:
            st.error(get_text(lang, 'error_model_not_trained', target=target))
            st.info(get_text(lang, 'error_train_command', target_lower=target_lower))
            st.stop()
        st.markdown(f"### {get_text(lang, 'upload_data')}")
        sample_file_path = Path("sample_files/sample_eclass_data.xlsx")
        if sample_file_path.exists():
            with open(sample_file_path, "rb") as f:
                sample_data = f.read()
            st.download_button(
                label=get_text(lang, 'download_sample'),
                data=sample_data,
                file_name="sample_eclass_data.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                help=get_text(lang, 'download_sample_help'),
                width='stretch'
            )
            st.caption(get_text(lang, 'sample_tip'))
        uploaded_file = st.file_uploader(
            get_text(lang, 'select_file'),
            type=['xlsx', 'xls', 'csv'],
            help=get_text(lang, 'select_file_help')
        )
    with col2:
        st.subheader(get_text(lang, 'prediction_results'))
        if uploaded_file is not None:
            st.info(get_text(lang, 'file_uploaded', filename=uploaded_file.name))
            if st.button(get_text(lang, 'start_prediction'), type="primary", width='stretch'):
                try:
                    with st.spinner(get_text(lang, 'processing')):
                        # 保存上傳的文件到臨時目錄
                        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                            tmp_file.write(uploaded_file.getvalue())
                            tmp_path = Path(tmp_file.name)
                        try:
                            # 使用按科目預測
                            subject_predictor = SubjectBasedPredictor(target=target_lower)
                            results = subject_predictor.predict_by_subject(tmp_path, model_path)
                            # 顯示結果
                            st.success(get_text(lang, 'prediction_complete'))
                            st.markdown("---")
                            # 格式化結果為表格
                            results_df = format_prediction_results(results, target_lower)
                            # 顯示總覽表格
                            st.subheader(get_text(lang, 'overview'))
                            st.dataframe(results_df, width='stretch', height=400)
                            st.markdown("---")
                            # 顯示每個學生的詳細預測結果（按科目）
                            st.subheader(get_text(lang, 'details'))
                            for result in results:
                                english_name = result['english_name']
                                student_id = result.get('student_id', english_name)
                                st.markdown(get_text(lang, 'student', name=english_name))
                                if student_id != english_name:
                                    st.caption(get_text(lang, 'student_id_label', id=student_id))
                                # 按科目顯示預測結果（排除 Average Score）
                                subjects_with_data = {k: v for k, v in result['subjects'].items()
                                                    if v['has_data'] and k.lower() not in ['average_score', 'average score', 'average']}
                                subjects_without_data = {k: v for k, v in result['subjects'].items()
                                                       if not v['has_data'] and k.lower() not in ['average_score', 'average score', 'average']}
                                if subjects_with_data:
                                    st.markdown(f"#### {get_text(lang, 'subjects_with_data')}")
                                    # 創建科目預測表格
                                    subject_data = []
                                    for subject, pred_data in subjects_with_data.items():
                                        subject_name = subject.replace('_', ' ').title()
                                        eclass_score = pred_data['eclass_score']
                                        predicted_score = pred_data['predicted_score']
                                        # 根據目標顯示等級
                                        if target_lower == 'hkdse':
                                            if predicted_score >= 5:
                                                grade = get_text(lang, 'hkdse_grades')['5**']
                                                color = "🟢"
                                            elif predicted_score >= 4.5:
                                                grade = get_text(lang, 'hkdse_grades')['5*']
                                                color = "🟢"
                                            elif predicted_score >= 4:
                                                grade = get_text(lang, 'hkdse_grades')['5']
                                                color = "🟢"
                                            elif predicted_score >= 3:
                                                grade = get_text(lang, 'hkdse_grades')['4']
                                                color = "🟡"
                                            elif predicted_score >= 2:
                                                grade = get_text(lang, 'hkdse_grades')['3']
                                                color = "🟡"
                                            elif predicted_score >= 1:
                                                grade = get_text(lang, 'hkdse_grades')['2']
                                                color = "🟠"
                                            else:
                                                grade = get_text(lang, 'hkdse_grades')['1']
                                                color = "🔴"
                                        else:  # IB
                                            grade_num = int(round(predicted_score))
                                            if grade_num >= 7:
                                                grade = get_text(lang, 'ib_grades')['7']
                                                color = "🟢"
                                            elif grade_num >= 6:
                                                grade = get_text(lang, 'ib_grades')['6']
                                                color = "🟢"
                                            elif grade_num >= 5:
                                                grade = get_text(lang, 'ib_grades')['5']
                                                color = "🟡"
                                            elif grade_num >= 4:
                                                grade = get_text(lang, 'ib_grades')['4']
                                                color = "🟡"
                                            else:
                                                grade = get_text(lang, 'ib_grades')['3']
                                                color = "🟠"
                                        subject_data.append({
                                            get_text(lang, 'subject'): subject_name,
                                            get_text(lang, 'eclass_avg'): f"{eclass_score:.1f}",
                                            get_text(lang, f'predicted_{target_lower}'): f"{predicted_score:.1f}",
                                            get_text(lang, 'predicted_grade'): f"{color} {grade}"
                                        })
                                    subject_df = pd.DataFrame(subject_data)
                                    st.dataframe(subject_df, width='stretch', hide_index=True)
                                if subjects_without_data:
                                    st.markdown(f"#### {get_text(lang, 'subjects_without_data')}")
                                    not_taken = [sub.replace('_', ' ').title() for sub in subjects_without_data.keys()]
                                    st.info(get_text(lang, 'not_taken_subjects', subjects=', '.join(not_taken)))
                                st.markdown("---")
                            # 下載結果
                            csv = results_df.to_csv(index=False)
                            st.download_button(
                                label=get_text(lang, 'download_results'),
                                data=csv,
                                file_name=f"{target}_predictions_by_subject.csv",
                                mime="text/csv"
                            )
                        finally:
                            # 清理臨時文件
                            if tmp_path.exists():
                                os.unlink(tmp_path)
                except Exception as e:
                    st.error(get_text(lang, 'error_prediction', error=str(e)))
                    st.exception(e)
        else:
            st.info(get_text(lang, 'error_no_file'))
    st.markdown("---")
    st.markdown(f"""
<div style='text-align: center; color: gray;'>
    <p>{get_text(lang, 'footer')}</p>
</div>
""", unsafe_allow_html=True)


# 自訂側邊欄頁面名稱（依目前語言只顯示一種）並啟動多頁導航
_nav_lang = st.session_state.get("language", "zh")
_pred_page = st.Page(_prediction_page, title=get_text(_nav_lang, "nav_score_prediction"), icon="📊", default=True)
_train_page = st.Page("pages/model_trainning.py", title=get_text(_nav_lang, "nav_train_model"), icon="🔧")
st.navigation([_pred_page, _train_page]).run()
