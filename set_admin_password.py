"""
設置管理員密碼工具

使用方法：
  python set_admin_password.py

功能：
  - 設置或更改管理員密碼
  - 生成密碼哈希值
  - 保存到文件或顯示環境變量設置命令
"""

import hashlib
import getpass
from pathlib import Path

ADMIN_PASSWORD_FILE = Path('.admin_password')

def hash_password(password: str) -> str:
    """生成密碼哈希"""
    return hashlib.sha256(password.encode()).hexdigest()

def set_password():
    """設置管理員密碼"""
    print("=" * 60)
    print("管理員密碼設置工具")
    print("=" * 60)
    print()
    
    # 檢查是否已有密碼文件
    if ADMIN_PASSWORD_FILE.exists():
        print("⚠️  檢測到已存在的密碼文件。")
        choice = input("是否要更改密碼？(y/n): ").strip().lower()
        if choice != 'y':
            print("操作已取消。")
            return
    
    # 輸入新密碼
    print("請輸入新的管理員密碼：")
    password = getpass.getpass("密碼: ")
    
    if not password:
        print("❌ 密碼不能為空！")
        return
    
    # 確認密碼
    password_confirm = getpass.getpass("確認密碼: ")
    
    if password != password_confirm:
        print("❌ 兩次輸入的密碼不一致！")
        return
    
    # 生成哈希
    password_hash = hash_password(password)
    
    # 保存到文件
    try:
        with open(ADMIN_PASSWORD_FILE, 'w') as f:
            f.write(password_hash)
        
        # 設置文件權限（僅所有者可讀寫）
        import os
        os.chmod(ADMIN_PASSWORD_FILE, 0o600)
        
        print()
        print("✅ 密碼設置成功！")
        print()
        print("密碼已保存到文件: .admin_password")
        print("文件權限已設置為僅所有者可讀寫。")
        print()
        print("=" * 60)
        print("安全提示：")
        print("=" * 60)
        print("1. 請妥善保管密碼文件")
        print("2. 不要將密碼文件提交到版本控制系統（已包含在 .gitignore）")
        print("3. 也可以使用環境變量設置密碼（更安全）：")
        print()
        print(f"   export ADMIN_PASSWORD_HASH='{password_hash}'")
        print()
        print("4. 如果使用環境變量，請刪除 .admin_password 文件")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ 保存密碼時出錯: {e}")

if __name__ == "__main__":
    try:
        set_password()
    except KeyboardInterrupt:
        print("\n\n操作已取消。")
    except Exception as e:
        print(f"\n❌ 發生錯誤: {e}")
