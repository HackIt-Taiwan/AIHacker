# 增強版內容審核系統更新指南

本次更新增加了增強的內容審核系統，提供更好的使用者體驗和自動化禁言處理機制。

## 更新內容

本次更新包含以下主要功能：

1. **增強的通知 UI/UX**：重新設計的違規通知，提供更清晰美觀的界面
2. **分級禁言系統**：根據違規次數自動實施不同時長的禁言
3. **社群規範整合**：基於 OpenAI 內容政策的詳細社群規範
4. **本地資料庫追蹤**：使用 SQLite 資料庫記錄違規和禁言資訊
5. **自動解除禁言**：臨時禁言期滿後自動恢復使用者權限

## 安裝步驟

### 1. 更新環境變數

在 `.env` 檔案中新增以下設定：

```env
# 內容審核配置
CONTENT_MODERATION_ENABLED=True
CONTENT_MODERATION_NOTIFICATION_TIMEOUT=10
CONTENT_MODERATION_BYPASS_ROLES=role_id1,role_id2
MUTE_ROLE_NAME=Muted
```

### 2. 新增檔案

以下檔案需要新增到專案中：

- `app/moderation_db.py` - 用於追蹤違規和禁言資訊的資料庫管理器
- `app/mute_manager.py` - 用於管理禁言系統的類別
- `app/community_guidelines.py` - 包含社群規範的定義
- `docs/enhanced_moderation.md` - 增強版審核系統的文檔
- `docs/community_guidelines.md` - 社群規範文檔

### 3. 更新 `config.py`

在 `app/config.py` 中新增以下設定：

```python
# 禁言角色名稱設定
MUTE_ROLE_NAME = os.getenv('MUTE_ROLE_NAME', 'Muted')
```

### 4. 更新 `main.py`

1. 在導入區塊新增 `MUTE_ROLE_NAME` 的導入
2. 新增全域變數 `mute_manager`
3. 在 `on_ready` 函數中初始化 `mute_manager`
4. 新增 `check_expired_mutes` 函數
5. 更新 `moderate_message` 函數以整合禁言功能和新的 UI

### 5. 資料庫設定

系統將自動創建所需的 SQLite 資料庫檔案，預設位置為 `data/moderation.db`。請確保 `data` 目錄存在且可寫入。

## 使用說明

### 違規處理流程

當使用者發送違規內容時，系統將：

1. 自動刪除違規訊息
2. 在頻道發送臨時通知（10秒後自動消失）
3. 發送詳細私訊給違規使用者
4. 根據違規次數自動實施禁言：
   - 第1次：禁言 5 分鐘
   - 第2次：禁言 12 小時
   - 第3次：禁言 7 天
   - 第4次：永久禁言

### 管理員操作

管理員可以：

1. 在 Discord 伺服器設定中調整 "Muted" 角色的權限
2. 手動移除使用者的 "Muted" 角色以解除禁言
3. 在 `.env` 檔案中設定 `CONTENT_MODERATION_BYPASS_ROLES` 為特定角色 ID，使其豁免審核

## 注意事項

1. 請確保 Bot 有管理角色的權限
2. 首次啟動時，系統將自動創建 "Muted" 角色並設定各頻道權限
3. 如有現有的內容審核舊資料，不會自動遷移至新系統
4. 系統會定期（每分鐘）檢查並解除已到期的禁言

## 開發人員備註

如需自定義禁言時間或違規處理邏輯，可修改 `app/moderation_db.py` 中的 `calculate_mute_duration` 方法。

## 相關文檔

- [增強版內容審核詳細文檔](../enhanced_moderation.md)
- [社群規範文檔](../community_guidelines.md) 