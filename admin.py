"""
管理員界面 - 數據上傳和模型訓練

功能：
  - 上傳新的訓練數據（eClass、HKDSE、IB）
  - 自動重新訓練模型
  - 查看模型性能指標
  - 數據預覽和驗證
"""

import streamlit as st
import pandas as pd
from pathlib import Path
import tempfile
import os
import shutil
from datetime import datetime
from predict_model import PredictionModel
import json
import hashlib
import getpass
import sys
import warnings
import atexit

# 抑制 Streamlit 關閉時的無害警告
warnings.filterwarnings("ignore", category=RuntimeWarning)

# 處理關閉時的 Event loop 錯誤
def suppress_event_loop_error():
    """抑制關閉時的 Event loop 錯誤"""
    import sys
    import threading
    
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

# 設置頁面配置
st.set_page_config(
    page_title="模型管理系統 / Model Management",
    page_icon="⚙️",
    layout="wide"
)

# 初始化 session state
if 'training_in_progress' not in st.session_state:
    st.session_state.training_in_progress = False
if 'last_training_results' not in st.session_state:
    st.session_state.last_training_results = {}
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'login_attempts' not in st.session_state:
    st.session_state.login_attempts = 0

# 密碼配置（可以從環境變量或配置文件讀取）
ADMIN_PASSWORD_HASH = os.environ.get('ADMIN_PASSWORD_HASH', None)
ADMIN_PASSWORD_FILE = Path('.admin_password')

def get_password_hash():
    """獲取管理員密碼哈希"""
    # 優先從環境變量讀取
    if ADMIN_PASSWORD_HASH:
        return ADMIN_PASSWORD_HASH
    
    # 從文件讀取
    if ADMIN_PASSWORD_FILE.exists():
        with open(ADMIN_PASSWORD_FILE, 'r') as f:
            return f.read().strip()
    
    # 默認密碼（首次使用時需要設置）
    # 默認密碼: admin123 (請在生產環境中更改)
    default_password = "admin123"
    return hashlib.sha256(default_password.encode()).hexdigest()

def verify_password(password: str) -> bool:
    """驗證密碼"""
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    return password_hash == get_password_hash()

def show_login_page():
    """顯示登錄頁面"""
    st.title("🔐 管理員登錄 / Admin Login")
    st.markdown("---")
    
    # 警告信息
    if st.session_state.login_attempts > 0:
        st.warning(f"⚠️ 登錄失敗，請重試。剩餘嘗試次數: {3 - st.session_state.login_attempts}")
    
    # 登錄表單
    with st.form("login_form"):
        st.markdown("### 請輸入管理員密碼")
        password = st.text_input(
            "密碼 / Password",
            type="password",
            help="輸入管理員密碼以訪問系統"
        )
        
        col1, col2 = st.columns([1, 4])
        with col1:
            submit_button = st.form_submit_button("🔑 登錄", use_container_width=True)
        
        if submit_button:
            if verify_password(password):
                st.session_state.authenticated = True
                st.session_state.login_attempts = 0
                st.success("✅ 登錄成功！")
                st.rerun()
            else:
                st.session_state.login_attempts += 1
                if st.session_state.login_attempts >= 3:
                    st.error("❌ 登錄失敗次數過多，請刷新頁面後重試。")
                    st.session_state.login_attempts = 0
                else:
                    st.error("❌ 密碼錯誤，請重試。")
                    st.rerun()
    
    # 密碼設置說明（僅在首次使用時顯示）
    if not ADMIN_PASSWORD_FILE.exists() and not ADMIN_PASSWORD_HASH:
        st.markdown("---")
        st.info("""
        **首次使用說明：**
        - 默認密碼：`admin123`
        - 建議立即更改密碼
        - 可以通過設置環境變量 `ADMIN_PASSWORD_HASH` 或創建 `.admin_password` 文件來設置自定義密碼
        """)
    
    # 側邊欄說明
    st.sidebar.markdown("### 🔒 安全提示")
    st.sidebar.info("""
    這是受保護的管理員界面。
    只有授權的管理員才能訪問。
    """)
    
    st.stop()  # 阻止繼續執行後續代碼

def show_logout_button():
    """顯示登出按鈕"""
    if st.sidebar.button("🚪 登出", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.login_attempts = 0
        st.rerun()

# 檢查登錄狀態
if not st.session_state.authenticated:
    show_login_page()

# 顯示登出按鈕
show_logout_button()

# 標題
st.title("🔧 模型管理系統 / Model Management System")
st.markdown("---")

# 側邊欄 - 導航
st.sidebar.title("📋 功能選單")
page = st.sidebar.radio(
    "選擇功能",
    ["數據上傳", "模型訓練", "模型性能", "數據管理"],
    index=0
)

# 數據目錄配置
DATA_DIR = Path("./Data")
ECLASS_DIR = DATA_DIR / "eClass Data"
HKDSE_DIR = DATA_DIR / "HKDSE"
IB_DIR = DATA_DIR / "IB"
MODEL_DIR = Path("./models")

# 確保目錄存在
for dir_path in [DATA_DIR, ECLASS_DIR, HKDSE_DIR, IB_DIR, MODEL_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)


def save_uploaded_file(uploaded_file, target_dir: Path, file_type: str):
    """保存上傳的文件"""
    try:
        # 生成帶時間戳的文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_ext = Path(uploaded_file.name).suffix
        new_filename = f"{timestamp}_{uploaded_file.name}"
        target_path = target_dir / new_filename
        
        # 保存文件
        with open(target_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        return target_path, None
    except Exception as e:
        return None, str(e)


def get_model_metrics(model_path: Path):
    """獲取模型性能指標（如果存在）"""
    metrics_file = model_path.parent / f"{model_path.stem}_metrics.json"
    if metrics_file.exists():
        with open(metrics_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


def save_model_metrics(model_path: Path, metrics: dict):
    """保存模型性能指標"""
    metrics_file = model_path.parent / f"{model_path.stem}_metrics.json"
    metrics['timestamp'] = datetime.now().isoformat()
    with open(metrics_file, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)


def count_data_files():
    """統計數據文件數量"""
    eclass_files = len(list(ECLASS_DIR.glob("*.xlsx")) + list(ECLASS_DIR.glob("*.xls")))
    hkdse_files = len(list(HKDSE_DIR.glob("**/*.xlsx")) + list(HKDSE_DIR.glob("**/*.xls")))
    ib_files = len(list(IB_DIR.glob("**/*.xlsx")) + list(IB_DIR.glob("**/*.xls")))
    return {
        'eclass': eclass_files,
        'hkdse': hkdse_files,
        'ib': ib_files
    }


# 頁面1: 數據上傳
if page == "數據上傳":
    st.header("📤 上傳訓練數據")
    st.markdown("上傳新的訓練數據文件，系統會自動保存並可用於模型訓練。")
    
    # 顯示當前數據統計
    st.subheader("📊 當前數據統計")
    file_counts = count_data_files()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("eClass 文件", file_counts['eclass'])
    with col2:
        st.metric("HKDSE 文件", file_counts['hkdse'])
    with col3:
        st.metric("IB 文件", file_counts['ib'])
    
    st.markdown("---")
    
    # 數據上傳區域
    tab1, tab2, tab3 = st.tabs(["📚 eClass 數據", "🎓 HKDSE 數據", "🌍 IB 數據"])
    
    with tab1:
        st.markdown("### 上傳 eClass 數據")
        st.info("上傳 eClass 成績數據文件（Excel 格式）")
        uploaded_eclass = st.file_uploader(
            "選擇 eClass 數據文件",
            type=['xlsx', 'xls'],
            key="eclass_uploader",
            help="支持 .xlsx 和 .xls 格式"
        )
        
        if uploaded_eclass is not None:
            # 預覽數據
            try:
                df_preview = pd.read_excel(uploaded_eclass, header=None, nrows=10)
                st.subheader("📋 數據預覽（前10行）")
                st.dataframe(df_preview, use_container_width=True)
                
                # 保存按鈕
                if st.button("💾 保存 eClass 數據", key="save_eclass"):
                    target_path, error = save_uploaded_file(uploaded_eclass, ECLASS_DIR, "eclass")
                    if error:
                        st.error(f"保存失敗: {error}")
                    else:
                        st.success(f"✅ 文件已保存: {target_path.name}")
                        st.rerun()
            except Exception as e:
                st.error(f"讀取文件失敗: {e}")
    
    with tab2:
        st.markdown("### 上傳 HKDSE 數據")
        st.info("上傳 HKDSE 成績數據文件（Excel 格式）")
        uploaded_hkdse = st.file_uploader(
            "選擇 HKDSE 數據文件",
            type=['xlsx', 'xls'],
            key="hkdse_uploader",
            help="支持 .xlsx 和 .xls 格式"
        )
        
        if uploaded_hkdse is not None:
            try:
                df_preview = pd.read_excel(uploaded_hkdse, nrows=10)
                st.subheader("📋 數據預覽（前10行）")
                st.dataframe(df_preview, use_container_width=True)
                
                if st.button("💾 保存 HKDSE 數據", key="save_hkdse"):
                    target_path, error = save_uploaded_file(uploaded_hkdse, HKDSE_DIR, "hkdse")
                    if error:
                        st.error(f"保存失敗: {error}")
                    else:
                        st.success(f"✅ 文件已保存: {target_path.name}")
                        st.rerun()
            except Exception as e:
                st.error(f"讀取文件失敗: {e}")
    
    with tab3:
        st.markdown("### 上傳 IB 數據")
        st.info("上傳 IB 成績數據文件（Excel 格式）")
        uploaded_ib = st.file_uploader(
            "選擇 IB 數據文件",
            type=['xlsx', 'xls'],
            key="ib_uploader",
            help="支持 .xlsx 和 .xls 格式"
        )
        
        if uploaded_ib is not None:
            try:
                df_preview = pd.read_excel(uploaded_ib, nrows=10)
                st.subheader("📋 數據預覽（前10行）")
                st.dataframe(df_preview, use_container_width=True)
                
                if st.button("💾 保存 IB 數據", key="save_ib"):
                    target_path, error = save_uploaded_file(uploaded_ib, IB_DIR, "ib")
                    if error:
                        st.error(f"保存失敗: {error}")
                    else:
                        st.success(f"✅ 文件已保存: {target_path.name}")
                        st.rerun()
            except Exception as e:
                st.error(f"讀取文件失敗: {e}")

# 頁面2: 模型訓練
elif page == "模型訓練":
    st.header("🚀 模型訓練")
    st.markdown("使用當前數據重新訓練預測模型。")
    
    # 顯示當前數據統計
    file_counts = count_data_files()
    st.subheader("📊 訓練數據統計")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("eClass 文件", file_counts['eclass'])
    with col2:
        st.metric("HKDSE 文件", file_counts['hkdse'])
    with col3:
        st.metric("IB 文件", file_counts['ib'])
    
    st.markdown("---")
    
    # 訓練選項
    st.subheader("⚙️ 訓練設置")
    col1, col2 = st.columns(2)
    
    with col1:
        target_choice = st.radio(
            "選擇訓練目標",
            ["HKDSE", "IB", "兩者都訓練"],
            help="選擇要訓練的模型類型"
        )
    
    with col2:
        test_size = st.slider(
            "測試集比例",
            min_value=0.1,
            max_value=0.4,
            value=0.2,
            step=0.05,
            help="用於測試的數據比例"
        )
    
    # 訓練按鈕
    if st.button("🎯 開始訓練模型", type="primary", use_container_width=True):
        if st.session_state.training_in_progress:
            st.warning("⚠️ 訓練正在進行中，請稍候...")
        else:
            st.session_state.training_in_progress = True
            
            targets = []
            if target_choice == "HKDSE" or target_choice == "兩者都訓練":
                targets.append('hkdse')
            if target_choice == "IB" or target_choice == "兩者都訓練":
                targets.append('ib')
            
            results = {}
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for idx, target in enumerate(targets):
                try:
                    status_text.text(f"正在訓練 {target.upper()} 模型...")
                    progress_bar.progress((idx + 1) / len(targets))
                    
                    # 創建模型並訓練
                    model = PredictionModel(target=target)
                    metrics = model.train(DATA_DIR, test_size=test_size)
                    
                    # 保存模型
                    model_path = MODEL_DIR / f"{target}_model.pkl"
                    model.save_model(model_path)
                    
                    # 保存指標
                    save_model_metrics(model_path, metrics)
                    
                    results[target] = {
                        'status': 'success',
                        'metrics': metrics
                    }
                    
                    st.success(f"✅ {target.upper()} 模型訓練完成！")
                    
                except Exception as e:
                    results[target] = {
                        'status': 'error',
                        'error': str(e)
                    }
                    st.error(f"❌ {target.upper()} 模型訓練失敗: {e}")
                    import traceback
                    st.code(traceback.format_exc())
            
            st.session_state.last_training_results = results
            st.session_state.training_in_progress = False
            progress_bar.empty()
            status_text.empty()
            
            st.balloons()
            st.success("🎉 訓練完成！請查看「模型性能」頁面查看詳細結果。")

# 頁面3: 模型性能
elif page == "模型性能":
    st.header("📈 模型性能指標")
    st.markdown("查看當前模型的性能指標和訓練歷史。")
    
    # 檢查模型是否存在
    hkdse_model = MODEL_DIR / "hkdse_model.pkl"
    ib_model = MODEL_DIR / "ib_model.pkl"
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎓 HKDSE 模型")
        if hkdse_model.exists():
            st.success("✅ 模型已訓練")
            
            # 顯示性能指標
            metrics = get_model_metrics(hkdse_model)
            if metrics:
                st.markdown("#### 性能指標")
                col1a, col1b = st.columns(2)
                with col1a:
                    st.metric("訓練集 MAE", f"{metrics.get('train_mae', 'N/A'):.3f}")
                    st.metric("訓練集 R²", f"{metrics.get('train_r2', 'N/A'):.3f}")
                with col1b:
                    st.metric("測試集 MAE", f"{metrics.get('test_mae', 'N/A'):.3f}")
                    st.metric("測試集 R²", f"{metrics.get('test_r2', 'N/A'):.3f}")
                
                if 'cv_mae' in metrics:
                    st.metric("交叉驗證 MAE", f"{metrics['cv_mae']:.3f} (±{metrics.get('cv_std', 0):.3f})")
                
                if 'timestamp' in metrics:
                    st.caption(f"最後訓練時間: {metrics['timestamp']}")
            else:
                st.info("暫無性能指標數據")
        else:
            st.error("❌ 模型未訓練")
            st.info("請前往「模型訓練」頁面訓練模型")
    
    with col2:
        st.subheader("🌍 IB 模型")
        if ib_model.exists():
            st.success("✅ 模型已訓練")
            
            # 顯示性能指標
            metrics = get_model_metrics(ib_model)
            if metrics:
                st.markdown("#### 性能指標")
                col2a, col2b = st.columns(2)
                with col2a:
                    st.metric("訓練集 MAE", f"{metrics.get('train_mae', 'N/A'):.3f}")
                    st.metric("訓練集 R²", f"{metrics.get('train_r2', 'N/A'):.3f}")
                with col2b:
                    st.metric("測試集 MAE", f"{metrics.get('test_mae', 'N/A'):.3f}")
                    st.metric("測試集 R²", f"{metrics.get('test_r2', 'N/A'):.3f}")
                
                if 'cv_mae' in metrics:
                    st.metric("交叉驗證 MAE", f"{metrics['cv_mae']:.3f} (±{metrics.get('cv_std', 0):.3f})")
                
                if 'timestamp' in metrics:
                    st.caption(f"最後訓練時間: {metrics['timestamp']}")
            else:
                st.info("暫無性能指標數據")
        else:
            st.error("❌ 模型未訓練")
            st.info("請前往「模型訓練」頁面訓練模型")
    
    # 顯示最近訓練結果
    if st.session_state.last_training_results:
        st.markdown("---")
        st.subheader("📊 最近訓練結果")
        for target, result in st.session_state.last_training_results.items():
            with st.expander(f"{target.upper()} 模型訓練結果"):
                if result['status'] == 'success':
                    metrics = result['metrics']
                    st.json(metrics)
                else:
                    st.error(f"訓練失敗: {result.get('error', '未知錯誤')}")

# 頁面4: 數據管理
elif page == "數據管理":
    st.header("🗂️ 數據文件管理")
    st.markdown("查看和管理已上傳的數據文件。")
    
    tab1, tab2, tab3 = st.tabs(["📚 eClass 文件", "🎓 HKDSE 文件", "🌍 IB 文件"])
    
    with tab1:
        st.subheader("eClass 數據文件")
        eclass_files = sorted(list(ECLASS_DIR.glob("*.xlsx")) + list(ECLASS_DIR.glob("*.xls")), 
                             key=lambda x: x.stat().st_mtime, reverse=True)
        
        if eclass_files:
            st.info(f"共 {len(eclass_files)} 個文件")
            
            for file_path in eclass_files:
                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        file_size = file_path.stat().st_size / 1024  # KB
                        mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                        st.text(f"📄 {file_path.name}")
                        st.caption(f"大小: {file_size:.1f} KB | 修改時間: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
                    
                    with col2:
                        if st.button("🗑️ 刪除", key=f"del_eclass_{file_path.name}"):
                            try:
                                file_path.unlink()
                                st.success("文件已刪除")
                                st.rerun()
                            except Exception as e:
                                st.error(f"刪除失敗: {e}")
                    
                    with col3:
                        with open(file_path, "rb") as f:
                            st.download_button(
                                "📥 下載",
                                f.read(),
                                file_path.name,
                                key=f"dl_eclass_{file_path.name}",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                    st.divider()
        else:
            st.info("暫無 eClass 數據文件")
    
    with tab2:
        st.subheader("HKDSE 數據文件")
        hkdse_files = sorted(list(HKDSE_DIR.glob("**/*.xlsx")) + list(HKDSE_DIR.glob("**/*.xls")),
                            key=lambda x: x.stat().st_mtime, reverse=True)
        
        if hkdse_files:
            st.info(f"共 {len(hkdse_files)} 個文件")
            
            for file_path in hkdse_files:
                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        file_size = file_path.stat().st_size / 1024
                        mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                        st.text(f"📄 {file_path.relative_to(HKDSE_DIR)}")
                        st.caption(f"大小: {file_size:.1f} KB | 修改時間: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
                    
                    with col2:
                        if st.button("🗑️ 刪除", key=f"del_hkdse_{file_path.name}"):
                            try:
                                file_path.unlink()
                                st.success("文件已刪除")
                                st.rerun()
                            except Exception as e:
                                st.error(f"刪除失敗: {e}")
                    
                    with col3:
                        with open(file_path, "rb") as f:
                            st.download_button(
                                "📥 下載",
                                f.read(),
                                file_path.name,
                                key=f"dl_hkdse_{file_path.name}",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                    st.divider()
        else:
            st.info("暫無 HKDSE 數據文件")
    
    with tab3:
        st.subheader("IB 數據文件")
        ib_files = sorted(list(IB_DIR.glob("**/*.xlsx")) + list(IB_DIR.glob("**/*.xls")),
                         key=lambda x: x.stat().st_mtime, reverse=True)
        
        if ib_files:
            st.info(f"共 {len(ib_files)} 個文件")
            
            for file_path in ib_files:
                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        file_size = file_path.stat().st_size / 1024
                        mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                        st.text(f"📄 {file_path.relative_to(IB_DIR)}")
                        st.caption(f"大小: {file_size:.1f} KB | 修改時間: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
                    
                    with col2:
                        if st.button("🗑️ 刪除", key=f"del_ib_{file_path.name}"):
                            try:
                                file_path.unlink()
                                st.success("文件已刪除")
                                st.rerun()
                            except Exception as e:
                                st.error(f"刪除失敗: {e}")
                    
                    with col3:
                        with open(file_path, "rb") as f:
                            st.download_button(
                                "📥 下載",
                                f.read(),
                                file_path.name,
                                key=f"dl_ib_{file_path.name}",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                    st.divider()
        else:
            st.info("暫無 IB 數據文件")

# 頁腳
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray;'>
    <p>模型管理系統 v1.0 | 使用 Streamlit 構建</p>
</div>
""", unsafe_allow_html=True)
