# 內容審核 API 更新文檔

**更新日期：** 2024年6月15日

## 更新概述

我們已對內容審核系統進行了更新，移除了預設的台灣口語表達詞彙庫白名單機制，改為完全依賴 AI 模型進行內容審核判斷。這一變更影響了審核流程和 API 的行為方式。

## API 變更說明

### `review_flagged_content` 函數變更

**路徑：** `app/ai/agents/moderation_review.py`

**變更前：**
```python
async def review_flagged_content(
    agent: Agent,
    content: str,
    violation_categories: List[str],
    context: Optional[str] = None,
    backup_agent: Optional[Agent] = None
) -> Dict[str, Any]:
    # 檢查內容是否為台灣常見口語表達
    taiwanese_expressions = [
        "想死", "快死了", "死了", "去死", "死翹翹", "爛死了",
        # ... 更多表達方式
    ]
    
    contains_taiwanese_expr = any(expr in content.lower() for expr in taiwanese_expressions)
    
    if contains_taiwanese_expr:
        return {
            "is_violation": False,
            "reason": f"內容包含台灣常見的口語表達方式，這通常是誇張表達而非真正的有害內容。根據文化語境，此內容應判定為誤判。",
            "original_response": "FALSE_POSITIVE: Taiwan colloquial expression"
        }
    
    # 後續審核流程...
```

**變更後：**
```python
async def review_flagged_content(
    agent: Agent,
    content: str,
    violation_categories: List[str],
    context: Optional[str] = None,
    backup_agent: Optional[Agent] = None
) -> Dict[str, Any]:
    # 直接進行 AI 審核流程，移除了預設白名單檢查
    # 檢查違規類型數量
    high_severity_count = len(violation_categories) >= 4
    
    # 後續審核流程...
```

## 使用變更

### 調用方式

調用內容審核功能的方式沒有改變，仍然使用相同的函數和參數：

```python
result = await review_flagged_content(
    agent=moderation_agent,
    content=message.content,
    violation_categories=violation_categories,
    context=context_messages
)
```

### 行為差異

1. **所有內容都經過 AI 評估**：所有被標記的內容現在都會經過 AI 審核評估，不再有自動判定為誤判的情況
2. **更加統一的判斷標準**：所有內容都使用相同的評估流程，避免基於特定詞彙的自動判定
3. **更依賴 AI 的語境理解**：系統現在完全依賴 AI 模型理解文本的語境和含義

## 返回值

返回值格式保持不變：

```python
{
    "is_violation": bool,  # 是否為真正的違規內容
    "reason": str,  # 判斷原因的說明
    "original_response": str  # AI 模型的原始回覆
}
```

## 部署注意事項

1. 此更新不需要修改資料庫結構或環境變數
2. 更新後請監控審核結果，確保系統正常運作
3. 如果發現誤判率顯著提高，可能需要調整 AI 模型的提示詞

## 可能的影響

1. **審核準確性**：可能出現短期內準確性略微變動的情況，隨著 AI 模型適應新的評估方式，準確性應會回升或提高
2. **審核延遲**：由於移除了快速預檢步驟，可能會導致審核處理時間略微增加
3. **資源消耗**：所有內容都需要經過 AI 評估，可能導致 API 調用次數增加

## 建議的整合方式

如果您的應用程序直接使用了內容審核 API，建議：

1. 確保您的應用程序能夠適當處理可能的延遲增加
2. 添加適當的錯誤處理和重試機制
3. 監控審核結果，收集用戶反饋以協助我們改進系統

如有任何問題或遇到異常情況，請立即聯繫技術支持團隊。

## 新的更新 (2024-06-24)

### 提醒和請假功能移除

移除了以下與提醒和請假相關的功能：

#### 已刪除的 API 模式

以下 AI 命令模式已被刪除，並將不再被處理：

```
[REMINDER]...[/REMINDER]            # 設置提醒
[LIST_REMINDERS]...[/LIST_REMINDERS] # 列出提醒
[DELETE_REMINDER]...[/DELETE_REMINDER] # 刪除提醒
[LEAVE]...[/LEAVE]                  # 請假申請
[LEAVE_LIST]...[/LEAVE_LIST]        # 列出請假
[LEAVE_DELETE]...[/LEAVE_DELETE]    # 刪除請假
```

#### 已移除的環境變數

```
REMINDER_CHECK_INTERVAL=60          # 提醒檢查間隔(秒)
LEAVE_ALLOWED_ROLES=role_id1,role_id2 # 允許請假的角色
LEAVE_ANNOUNCEMENT_CHANNEL_IDS=channel_id1,channel_id2 # 請假公告頻道
```

#### 已刪除的資料庫

```
data/reminders.db                   # 提醒資料庫
data/leaves.db                      # 請假資料庫
```

#### 遷移指南

不再支援提醒和請假功能。用戶需要使用替代的系統來管理提醒和請假。

## Docker 部署支援 (2024-03-31)

### 概述

AIHacker Discord Bot 現在支援 Docker 容器化部署，透過 Docker 和 Docker Compose 可以輕鬆在任何支援 Docker 的平台上運行機器人。

### 主要檔案

- `Dockerfile` - 定義了如何構建 Docker 映像
- `docker-compose.yml` - 定義了如何運行容器和管理依賴
- `.dockerignore` - 指定哪些檔案不包含在 Docker 構建上下文中

### 使用方法

#### 基本部署

```bash
# 複製環境變數範例檔案
cp .env.example .env

# 編輯 .env 檔案，填入必要的設定值
nano .env

# 使用 Docker Compose 啟動服務
docker-compose up -d
```

#### 檢視日誌

```bash
# 查看即時日誌
docker-compose logs -f
```

#### 更新服務

```bash
# 拉取最新代碼
git pull

# 重建並重啟容器
docker-compose down
docker-compose up -d --build
```

### 資料持久化

為確保資料持久性，Docker 設定將以下目錄映射為卷：

- `./data:/app/data` - 存儲資料庫檔案
- `./logs:/app/logs` - 存儲日誌檔案
- `./.env:/app/.env` - 環境設定檔案

### 安全性考慮

Docker 容器使用非特權使用者 `botuser` 執行應用程式，遵循最佳實踐以增強安全性。

### 進階設定

可通過編輯 `docker-compose.yml` 檔案調整以下設定：

- 時區設定 (`TZ=Asia/Taipei`)
- 重啟策略 (`restart: unless-stopped`)
- 健康檢查參數

詳細的部署說明請參考 [Docker 部署指南](docker_deployment.md)。 