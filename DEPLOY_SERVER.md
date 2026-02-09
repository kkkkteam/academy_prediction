# 學校自架伺服器部署指南

本指南說明如何在校內 Linux 伺服器上部署「學生成績預測」Streamlit 應用，並（可選）用 Nginx 做反向代理與 HTTPS。

---

## 一、伺服器需求

- **作業系統**：Linux（Ubuntu 20.04+ / Debian 11+ / CentOS 7+ 等）
- **Python**：3.8 或以上
- **權限**：能安裝套件（apt/yum）及建立 systemd 服務（或請 IT 協助）

---

## 二、把專案放到伺服器

任選一種方式把整個專案目錄放到伺服器（例如 `/opt/student-prediction`）：

**方式 A：用 Git（推薦）**

```bash
sudo mkdir -p /opt/student-prediction
sudo chown $USER:$USER /opt/student-prediction
cd /opt/student-prediction
git clone https://github.com/你的帳號/你的repo.git .
```

**方式 B：用 scp 上傳**

在本機執行（把 `user@server` 改成實際帳號與主機）：

```bash
scp -r "/Users/kayng/Desktop/HKCCCU Logos Academy/Program" user@伺服器IP:/opt/student-prediction
```

上傳後在伺服器上進入目錄：

```bash
ssh user@伺服器IP
cd /opt/student-prediction
```

---

## 三、安裝 Python 與依賴（在伺服器上執行）

### 3.1 確認 Python 版本

```bash
python3 --version   # 需 3.8+
```

若版本太舊，請用系統套件安裝較新版本，例如（Ubuntu/Debian）：

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv
```

### 3.2 建立虛擬環境並安裝依賴

```bash
cd /opt/student-prediction
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 四、訓練模型（二選一）

### 選項 A：在本機訓練，只把模型檔傳到伺服器

在本機執行訓練後，把 `models/` 裡的 `.pkl` 複製到伺服器：

```bash
# 本機
scp models/hkdse_model.pkl models/ib_model.pkl user@伺服器IP:/opt/student-prediction/models/
```

### 選項 B：在伺服器上訓練

若訓練資料可以放在伺服器上：

1. 在伺服器建立資料夾並放入資料：
   ```bash
   mkdir -p /opt/student-prediction/Data/{eClass\ Data,HKDSE,IB}
   # 把對應的 xlsx/xls 放到 Data/eClass Data、Data/HKDSE、Data/IB
   ```
2. 在專案目錄下、已啟動 venv 的環境執行：
   ```bash
   cd /opt/student-prediction
   source venv/bin/activate
   python train_model.py --target both --data-dir ./Data
   ```

確認有產生 `models/hkdse_model.pkl` 和 `models/ib_model.pkl`。

---

## 五、直接執行 Streamlit（先測試）

在專案目錄、已 `source venv/bin/activate` 的 shell 裡執行：

```bash
cd /opt/student-prediction
source venv/bin/activate
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

- `--server.address 0.0.0.0`：允許其他電腦透過 IP 連線（不只本機）
- `--server.port 8501`：使用 8501 port（可改成學校允許的 port）

用瀏覽器打開：`http://伺服器IP:8501`，能正常使用即可。  
測試完用 `Ctrl+C` 關閉，再依下面步驟做成常駐服務。

---

## 六、設成常駐服務（開機自動啟動）

用 **systemd** 讓 Streamlit 在背景常駐，重開機後也會自動啟動。

### 6.1 建立 systemd 服務檔

```bash
sudo nano /etc/systemd/system/streamlit-prediction.service
```

貼上以下內容（路徑請依實際修改）：

```ini
[Unit]
Description=Streamlit Student Prediction App
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/student-prediction
Environment="PATH=/opt/student-prediction/venv/bin"
ExecStart=/opt/student-prediction/venv/bin/streamlit run app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

注意：

- **User/Group**：若不用 `www-data`，改成實際執行此程式的帳號（例如 `deploy`）。
- **WorkingDirectory / PATH / ExecStart**：若專案不在 `/opt/student-prediction`，請改成實際路徑。
- 若專案目錄權限只給某個使用者，就把 `User=` 改成該使用者（例如 `User=deploy`），並確保該使用者能讀寫 `models/` 與上傳暫存檔。

### 6.2 啟動並設為開機啟動

```bash
sudo systemctl daemon-reload
sudo systemctl enable streamlit-prediction
sudo systemctl start streamlit-prediction
sudo systemctl status streamlit-prediction
```

看到 `active (running)` 即表示成功。之後可用：

- `sudo systemctl stop streamlit-prediction` 停止  
- `sudo systemctl restart streamlit-prediction` 重啟  
- `sudo journalctl -u streamlit-prediction -f` 看即時日誌  

此時可透過 `http://伺服器IP:8501` 使用。

---

## 七、（可選）Nginx 反向代理 + HTTPS

若希望用網域（例如 `predict.school.edu.hk`）且走 HTTPS，可在同一台或另一台機器上架 Nginx，把 80/443 轉到本機 8501。

### 7.1 安裝 Nginx 與憑證工具（Ubuntu/Debian）

```bash
sudo apt update
sudo apt install -y nginx certbot python3-certbot-nginx
```

### 7.2 新增 Nginx 站台設定

```bash
sudo nano /etc/nginx/sites-available/student-prediction
```

內容範例（請把 `predict.school.edu.hk` 改成你的網域）：

```nginx
server {
    listen 80;
    server_name predict.school.edu.hk;

    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
```

啟用站台並測試設定：

```bash
sudo ln -s /etc/nginx/sites-available/student-prediction /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 7.3 申請 SSL 憑證（Let's Encrypt）

```bash
sudo certbot --nginx -d predict.school.edu.hk
```

依提示完成後，Nginx 會自動改為 443 並設定憑證。之後用 `https://predict.school.edu.hk` 即可存取。

---

## 八、防火牆

若校內有防火牆，需開放對外提供服務的 port：

- **只開 8501**（直接連 Streamlit）：開放 8501
- **用 Nginx**：對外只開 80、443，Nginx 內部轉到 8501

例如（ufw）：

```bash
sudo ufw allow 8501    # 若直接對外開 Streamlit
# 或
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

---

## 九、更新應用或模型

程式或模型更新後：

```bash
cd /opt/student-prediction
source venv/bin/activate

# 若用 Git
git pull

# 若在本機訓練、只更新模型
# 本機：scp models/*.pkl user@伺服器:/opt/student-prediction/models/

# 若在伺服器上重新訓練
# python train_model.py --target both --data-dir ./Data

# 重啟服務
sudo systemctl restart streamlit-prediction
```

---

## 十、快速指令整理

| 項目           | 指令 |
|----------------|------|
| 進入專案目錄   | `cd /opt/student-prediction` |
| 啟動虛擬環境   | `source venv/bin/activate` |
| 手動執行測試   | `streamlit run app.py --server.port 8501 --server.address 0.0.0.0` |
| 啟動服務       | `sudo systemctl start streamlit-prediction` |
| 停止服務       | `sudo systemctl stop streamlit-prediction` |
| 重啟服務       | `sudo systemctl restart streamlit-prediction` |
| 看狀態         | `sudo systemctl status streamlit-prediction` |
| 看日誌         | `sudo journalctl -u streamlit-prediction -f` |

若你提供學校伺服器的 OS（例如 Ubuntu 22.04）與網域，我可以依你的環境改一版更貼合你校的指令與路徑。
