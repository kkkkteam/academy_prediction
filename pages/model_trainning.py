"""
訓練模型獨立頁面 - 需輸入密碼後才能使用
"""
import streamlit as st
import tempfile
import os
import hashlib
from pathlib import Path
from predict_model import PredictionModel
from language import get_text

st.set_page_config(
    page_title="訓練模型 / Train Model",
    page_icon="🔧",
    layout="wide"
)

# 密碼驗證（與 admin / set_admin_password 一致）
ADMIN_PASSWORD_FILE = Path(".admin_password")

def get_password_hash():
    if os.environ.get("ADMIN_PASSWORD_HASH"):
        return os.environ.get("ADMIN_PASSWORD_HASH")
    if ADMIN_PASSWORD_FILE.exists():
        return ADMIN_PASSWORD_FILE.read_text().strip()
    # 首次使用預設（請務必執行 set_admin_password.py 更改）
    return hashlib.sha256("admin123".encode()).hexdigest()

def verify_password(password: str) -> bool:
    if not password:
        return False
    return hashlib.sha256(password.encode()).hexdigest() == get_password_hash()

def save_password_hash(new_hash: str) -> bool:
    """將新密碼雜湊寫入檔案（僅當未使用環境變數時）"""
    if os.environ.get("ADMIN_PASSWORD_HASH"):
        return False
    try:
        ADMIN_PASSWORD_FILE.write_text(new_hash)
        import os as _os
        _os.chmod(ADMIN_PASSWORD_FILE, 0o600)
        return True
    except Exception:
        return False

# Session state（與主 app 共用 language，側邊欄會依此顯示對應語言）
if "train_authenticated" not in st.session_state:
    st.session_state.train_authenticated = False
if "language" not in st.session_state:
    st.session_state.language = "zh"

lang = st.session_state.language

# 未登入：顯示密碼表單
if not st.session_state.train_authenticated:
    # 語言切換固定右上角
    _c1, _c2 = st.columns([5, 1])
    with _c2:
        _lang_choice = st.selectbox(
            "🌐 語言 / Language",
            options=["zh", "en"],
            index=0 if lang == "zh" else 1,
            format_func=lambda x: "中文" if x == "zh" else "English",
            key="train_login_lang"
        )
        if _lang_choice != lang:
            st.session_state.language = _lang_choice
            st.rerun()
    st.title(get_text(lang, "train_login_title"))
    st.markdown("---")
    with st.form("train_login_form"):
        st.markdown(get_text(lang, "train_login_prompt"))
        pwd = st.text_input(get_text(lang, "train_login_password"), type="password", key="train_pwd")
        submitted = st.form_submit_button(get_text(lang, "train_login_button"))
        if submitted:
            if verify_password(pwd):
                st.session_state.train_authenticated = True
                st.rerun()
            else:
                st.error(get_text(lang, "train_login_failed"))
    st.markdown("---")
    with st.expander(get_text(lang, "train_change_password")):
        if os.environ.get("ADMIN_PASSWORD_HASH"):
            st.info(get_text(lang, "train_change_env_only"))
        else:
            with st.form("change_password_form"):
                current = st.text_input(get_text(lang, "train_current_password"), type="password", key="chpwd_current")
                new_pwd = st.text_input(get_text(lang, "train_new_password"), type="password", key="chpwd_new")
                confirm = st.text_input(get_text(lang, "train_confirm_password"), type="password", key="chpwd_confirm")
                if st.form_submit_button(get_text(lang, "train_change_password_submit")):
                    if not verify_password(current):
                        st.error(get_text(lang, "train_change_wrong_current"))
                    elif new_pwd != confirm:
                        st.error(get_text(lang, "train_change_mismatch"))
                    elif not new_pwd:
                        st.error(get_text(lang, "train_change_empty"))
                    else:
                        new_hash = hashlib.sha256(new_pwd.encode()).hexdigest()
                        if save_password_hash(new_hash):
                            st.success(get_text(lang, "train_change_success"))
                        else:
                            st.error(get_text(lang, "train_change_env_only"))
    st.stop()

# 已登入：顯示訓練模型內容（語言固定右上角，登出在語言下方）
_c1, _c2 = st.columns([5, 1])
with _c2:
    lang_choice = st.selectbox(
        "🌐 語言 / Language",
        options=["zh", "en"],
        index=0 if lang == "zh" else 1,
        format_func=lambda x: "中文" if x == "zh" else "English",
        key="train_lang_select"
    )
    if lang_choice != lang:
        st.session_state.language = lang_choice
        st.rerun()
    if st.button("🚪 登出", key="train_logout", use_container_width=True):
        st.session_state.train_authenticated = False
        st.rerun()
st.title(get_text(lang, "train_page_title"))
st.markdown("---")
st.subheader(get_text(lang, "train_title"))
st.markdown(get_text(lang, "train_intro"))
st.markdown("---")

model_dir = Path("./models")
hkdse_model_path = model_dir / "hkdse_model.pkl"
ib_model_path = model_dir / "ib_model.pkl"
model_dir.mkdir(parents=True, exist_ok=True)

train_eclass = st.file_uploader(
    get_text(lang, "train_eclass_label"),
    type=["xlsx", "xls"],
    help=get_text(lang, "train_eclass_help"),
    accept_multiple_files=True,
)
train_hkdse_file = st.file_uploader(
    get_text(lang, "train_hkdse_label"),
    type=["xlsx", "xls"],
    key="train_hkdse",
)
train_ib_file = st.file_uploader(
    get_text(lang, "train_ib_label"),
    type=["xlsx", "xls"],
    key="train_ib",
)
train_target = st.radio(
    get_text(lang, "train_target_label"),
    [
        get_text(lang, "train_target_hkdse"),
        get_text(lang, "train_target_ib"),
        get_text(lang, "train_target_both"),
    ],
    key="train_target_radio",
)
if train_target == get_text(lang, "train_target_hkdse"):
    train_target_val = "hkdse"
elif train_target == get_text(lang, "train_target_ib"):
    train_target_val = "ib"
else:
    train_target_val = "both"

if st.button(get_text(lang, "train_button"), type="primary", key="train_btn"):
    need_hkdse = train_target_val in ("hkdse", "both")
    need_ib = train_target_val in ("ib", "both")
    if not train_eclass or len(train_eclass) == 0:
        st.error(get_text(lang, "train_error_missing", target="HKDSE/IB"))
    elif need_hkdse and not train_hkdse_file:
        st.error(get_text(lang, "train_error_missing", target="HKDSE"))
    elif need_ib and not train_ib_file:
        st.error(get_text(lang, "train_error_missing", target="IB"))
    else:
        try:
            with st.spinner(get_text(lang, "processing")):
                with tempfile.TemporaryDirectory() as tmpdir:
                    data_dir = Path(tmpdir)
                    (data_dir / "eClass Data").mkdir()
                    (data_dir / "HKDSE").mkdir()
                    (data_dir / "IB").mkdir()
                    for f in train_eclass:
                        (data_dir / "eClass Data" / f.name).write_bytes(f.getvalue())
                    if train_hkdse_file:
                        (data_dir / "HKDSE" / train_hkdse_file.name).write_bytes(
                            train_hkdse_file.getvalue()
                        )
                    if train_ib_file:
                        (data_dir / "IB" / train_ib_file.name).write_bytes(
                            train_ib_file.getvalue()
                        )
                    targets = (
                        ["hkdse", "ib"]
                        if train_target_val == "both"
                        else [train_target_val]
                    )
                    for t in targets:
                        model = PredictionModel(target=t)
                        model.train(data_dir, test_size=0.2)
                        model.save_model(model_dir / f"{t}_model.pkl")
            st.success(get_text(lang, "train_success"))
            st.caption(get_text(lang, "train_download_tip"))
            col_h, col_i = st.columns(2)
            with col_h:
                if hkdse_model_path.exists():
                    pkl_data = hkdse_model_path.read_bytes()
                    st.download_button(
                        get_text(lang, "train_download_hkdse"),
                        data=pkl_data,
                        file_name="hkdse_model.pkl",
                        mime="application/octet-stream",
                        key="dl_hkdse",
                    )
            with col_i:
                if ib_model_path.exists():
                    pkl_data = ib_model_path.read_bytes()
                    st.download_button(
                        get_text(lang, "train_download_ib"),
                        data=pkl_data,
                        file_name="ib_model.pkl",
                        mime="application/octet-stream",
                        key="dl_ib",
                    )
        except Exception as e:
            st.error(get_text(lang, "train_error_failed", error=str(e)))
            st.exception(e)

st.markdown("---")
st.markdown(f"### {get_text(lang, 'train_sample_section')}")
st.caption(get_text(lang, "train_sample_tip"))
sample_dir = Path("sample_files")
col_s1, col_s2, col_s3 = st.columns(3)
with col_s1:
    sample_eclass = sample_dir / "sample_eclass_data.xlsx"
    if sample_eclass.exists():
        st.download_button(
            get_text(lang, "train_download_sample_eclass"),
            data=sample_eclass.read_bytes(),
            file_name=sample_eclass.name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="dl_sample_eclass",
        )
with col_s2:
    sample_hkdse = sample_dir / "sample_hkdse_results.xlsx"
    if sample_hkdse.exists():
        st.download_button(
            get_text(lang, "train_download_sample_hkdse"),
            data=sample_hkdse.read_bytes(),
            file_name=sample_hkdse.name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="dl_sample_hkdse",
        )
with col_s3:
    sample_ib = sample_dir / "sample_ib_results.xlsx"
    if sample_ib.exists():
        st.download_button(
            get_text(lang, "train_download_sample_ib"),
            data=sample_ib.read_bytes(),
            file_name=sample_ib.name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="dl_sample_ib",
        )
