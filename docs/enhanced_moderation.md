# 增強的內容審核系統

HackIt Discord Bot 現在支援更強大的內容審核和自動違規處置功能，使用 OpenAI 的 omni-moderation-latest 模型配合分級禁言系統，提供極佳的使用者體驗。

## 主要特點

- **增強的 UI/UX**：更精美的通知設計，清晰呈現違規資訊
- **分級禁言制度**：根據違規次數自動實施對應的禁言處罰
- **完整的社群規範**：基於 OpenAI 內容政策的詳細社群規範
- **本地資料庫追蹤**：使用 SQLite 資料庫儲存違規記錄
- **自動解除禁言**：臨時禁言期滿後自動恢復使用者權限

## 分級禁言制度

系統會自動記錄使用者違規次數，並根據次數實施以下禁言處罰：

1. **第 1 次違規**：禁言 5 分鐘
2. **第 2 次違規**：禁言 12 小時
3. **第 3 次違規**：禁言 7 天
4. **第 4 次違規**：禁言 7 天
5. **第 5 次及以上違規**：禁言 28 天

禁言通過 Discord 內建的超時（Timeout）功能實現，被禁言的使用者在所有頻道中都無法發送訊息、加入語音頻道或進行其他互動。

## 配置說明

在 `.env` 文件中可以設定以下參數：

```env
# 內容審核配置
OPENAI_API_KEY=your_openai_api_key_here
CONTENT_MODERATION_ENABLED=True
CONTENT_MODERATION_NOTIFICATION_TIMEOUT=10
CONTENT_MODERATION_BYPASS_ROLES=role_id1,role_id2
MUTE_ROLE_NAME=Muted
```

- `CONTENT_MODERATION_ENABLED`：是否啟用內容審核 (True/False)
- `CONTENT_MODERATION_NOTIFICATION_TIMEOUT`：頻道臨時通知的顯示時間（秒）
- `CONTENT_MODERATION_BYPASS_ROLES`：可繞過審核的角色 ID，用逗號分隔
- `MUTE_ROLE_NAME`：用於禁言的角色名稱

## 使用者體驗

### 違規通知流程

當使用者發送違規內容時：

1. **即時刪除**：系統立即刪除違規訊息
2. **頻道通知**：在訊息頻道顯示簡短通知（10秒後自動消失）
3. **詳細私訊**：向使用者發送私訊，包含違規詳情和處罰說明
4. **自動禁言**：根據違規次數自動實施相應的禁言

### 通知設計

#### 頻道通知

頻道通知採用簡潔設計，包括：
- 警示標題與圖標
- 違規用戶標記
- 通知將在短時間內自動消失的提示
- 指示更多詳情已通過私訊發送

#### 私訊通知

私訊通知採用豐富的 Embed 設計，包括：
- 伺服器圖標與標識
- 違規類型（配有表情符號指示）
- 違規內容摘要
- 禁言處罰詳情
- 違規次數統計
- 社群規範引用
- 申訴方式說明

## 社群規範

系統內建完整的社群規範，涵蓋 OpenAI 審核模型識別的所有違規類型：

- 騷擾內容
- 威脅性騷擾
- 仇恨言論
- 威脅性仇恨言論
- 自我傷害相關內容
- 性相關不當內容
- 暴力內容
- 非法活動相關內容
- 等等

每當使用者違規時，系統會引用對應的社群規範條目，幫助使用者理解哪些行為不被允許。

## 技術實現

增強的內容審核系統主要包括以下元件：

1. **app/ai/service/moderation.py**：使用 OpenAI API 進行內容審核
2. **app/moderation_db.py**：管理違規和禁言記錄
3. **app/mute_manager.py**：負責禁言實施和管理
4. **app/community_guidelines.py**：定義社群規範
5. **main.py**：整合上述組件並處理事件

系統自動檢查過期的禁言記錄，確保臨時禁言在指定時間後自動解除。

### 違規類別對應

系統支援所有 OpenAI 審核 API 返回的違規類型，包括兩種格式：

1. **下劃線格式**（API 返回的原始格式）：
   - harassment_threatening
   - self_harm
   - self_harm_intent
   - illicit_violent
   - 等等

2. **斜線格式**（傳統格式）：
   - harassment/threatening
   - self-harm
   - self-harm/intent
   - illicit/violent
   - 等等

所有類別都會被正確翻譯成繁體中文並在通知中顯示。詳情請參閱 [違規類別對應更新文件](updates/category_mapping_update.md)。

### 審核複查系統

為了減少誤判和提高審核準確度，系統配備了智能審核複查功能：

1. **自動複查**：被 OpenAI 審核 API 標記的內容會由 AI 代理再次評估
2. **上下文理解**：考慮訊息的上下文和文化因素
3. **誤判防護**：識別歌曲名稱、書名、專業術語等易被誤判的內容
4. **詳細解釋**：提供清晰的審核結果解釋，說明處罰或免除處罰的理由

該功能特別有助於避免對包含無害文化內容（如「跳樓機」這類歌曲名稱）的訊息誤判為違規。詳情請參閱 [審核複查系統文件](updates/moderation_review.md)。

### 性能優化

為了確保審核系統的穩定性和效能，我們進行了以下優化：

1. **即時禁言處理**：優化了審核流程，確保刪除違規訊息後立即執行禁言處理，而不受其他操作影響
2. **JSON序列化改進**：解決了 Categories 對象序列化問題，確保所有違規記錄能夠正確存入資料庫
3. **增強錯誤處理**：添加了更完善的錯誤捕獲和日誌記錄機制，提高系統穩定性

詳情請參閱 [審核系統修復文件](updates/moderation_fixes.md)。

## 工作人員指南

工作人員不需要手動管理禁言，系統會自動處理。但工作人員可以手動調整：

1. 在 Discord 管理面板中調整 "Muted" 角色權限
2. 手動解除特定使用者的禁言（移除 "Muted" 角色）
3. 通過設定 `CONTENT_MODERATION_BYPASS_ROLES` 為特定角色豁免審核

## 最佳實踐

1. 確保 "Muted" 角色在所有頻道中設置了正確的權限
2. 定期確認系統處理的違規統計，以評估社群健康度
3. 考慮在歡迎訊息中包含社群規範的簡短介紹和完整規範的連結

這個增強的內容審核系統有助於維護健康的社區環境，同時提供清晰透明的使用者體驗，讓使用者了解違規原因和相應的處理措施。