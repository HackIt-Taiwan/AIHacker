# AI Hacker Discord Bot

## 最近更新

### URL安全檢查系統增強：短網址黑名單映射 (2024-03-26)
- 更新URL黑名單系統，現在同時記錄原始短網址和展開後的目標URL
- 大幅提高對已知短網址的處理效率，無需展開即可識別危險短網址
- 為所有處理過的短網址建立映射關係，加速後續檢查
- 更詳細資訊請查看 [URL黑名單功能增強文檔](docs/updates/shortened_url_blacklist_update.md)

### URL安全檢查系統新增URL黑名單功能 (2024-03-26)
- 新增URL黑名單系統，自動記錄已檢測到的危險URL
- 提高安全檢查效率，已知威脅無需再重複API檢查
- 支援網域黑名單，可自動封鎖嚴重威脅的整個網域
- 使用持久化JSON存儲，確保重啟後黑名單仍然有效
- 更詳細資訊請查看 [URL黑名單功能文檔](docs/url_blacklist.md)

### URL安全檢查系統新增URL展開功能 (2024-03-26)
- 新增URL短網址展開功能，以提高安全檢查的有效性
- 使用多種方法展開短網址，包括HTTP請求和Selenium無頭瀏覽器
- 智能處理各種URL縮短服務，如bit.ly、tinyurl.com等
- 支援JavaScript重定向和多層次URL跳轉追蹤
- 更詳細資訊請查看 [URL展開功能文檔](docs/url_unshortening.md)

### URL安全檢查系統新增隨機抽樣功能 (2024-07-30)
- 當用戶一次發送超過設定數量的連結時，系統只會隨機抽查部分連結
- 新增 URL_SAFETY_MAX_URLS 環境變數，用於設定最大檢查數量
- 優化處理效率，減少 API 請求次數
- 更詳細資訊請查看 [URL安全檢查抽樣功能文檔](docs/updates/url_safety_sampling.md)

### URL安全檢查系統簡化 (2024-07-29)
- 移除短網址擴展功能，降低系統複雜度
- 移除自定義威脅檢測邏輯，專注於 VirusTotal API 整合
- 提高整體效能和可靠性
- 更詳細資訊請查看 [URL安全系統簡化文檔](docs/updates/url_safety_simplification.md)

### URL安全檢查系統優化：進階威脅偵測 (2024-07-28)
- 增加頁面內容啟發式分析，有效偵測釣魚網站和欺詐頁面
- 實現可疑域名識別，檢測潛在惡意網域
- 整合 URL 參數分析，發現隱藏在參數中的威脅
- 強化短網址處理機制，對未成功展開的短網址進行特殊處理
- 建立多層威脅評分系統，提供詳細的威脅情報
- 更詳細資訊請查看 [URL安全進階威脅偵測文檔](docs/updates/url_safety_enhancement_v3.md)

### URL安全檢查系統優化：本地遞迴網址展開 (2024-07-27)
- 實現了本地遞迴URL展開系統，不再依賴外部API
- 能夠偵測並有效處理各類URL短網址，包括shorturl.at和reurl.cc
- 支援多層次重定向的追蹤，包含HTTP重定向、meta刷新和JavaScript重定向
- 增強對特定URL短網址服務的模式檢測
- 新增訪問過的URL追蹤以防止重定向循環
- 更詳細資訊請查看 [URL安全本地展開增強文檔](docs/updates/url_safety_enhancement_v2.md)

### URL安全檢查完全重寫 (2024-07-25)
- 完全重寫 URL 安全檢查系統，大幅提升短網址偵測和追蹤能力
- 實現更高效的短網址解析和多重重定向追蹤
- 提升對域名偽裝和可疑路徑的檢測能力
- 實現並行處理多個 URL 的檢查，提高效率
- 更詳細資訊請查看 [URL安全模組增強文檔](docs/updates/url_safety_enhancement.md)

### URL安全檢查改進 - 重定向處理 (2024-07-11)
- 增強短網址和重定向URL的安全性檢查功能
- 使用GET請求代替HEAD請求，更有效地跟踪URL重定向
- 添加對Meta refresh重定向的檢測和跟踪
- 改進相對URL路徑的處理
- 更詳細資訊請查看 [URL重定向處理改進文檔](docs/updates/url_safety_improvements_redirects.md)

### 登入通知系統優化 (2024-06-26)
- 增強機器人登入和初始化完成通知的可見性
- 改進日誌系統配置，確保所有日誌都正確記錄
- 自動創建日誌目錄並使用 UTF-8 編碼
- 更詳細資訊請查看 [登入通知改進文檔](docs/updates/login_notification_enhancement.md)

### 修復異步生成器語法和類初始化問題 (2024-06-25)
- 修復 `ai_handler.py` 中的異步生成器語法錯誤
- 修復 `QuestionManager` 和 `NotionFAQ` 類的初始化參數不匹配問題
- 修復 `moderation_queue.py` 中缺少的內容審核隊列啟動函數
- 更詳細資訊請查看 [修復文檔](docs/updates/async_generator_fix.md)

### 移除提醒與請假功能 (2024-06-24)
- 移除提醒和請假相關功能以簡化系統
- 更詳細資訊請查看 [功能移除文檔](docs/updates/remove_reminder_leave.md)

### 超時功能更新：使用 Discord 內建禁言功能 (2024-06-20)
- 更新為使用 Discord 內建的超時功能替代角色禁言
- 新增 `/timeout` 和 `/remove_timeout` 命令
- 更詳細資訊請查看 [管理工具使用指南](docs/moderation.md)

### 審核系統更新：移除白名單 (2024-06-15)
- 移除台灣口語表達詞彙庫白名單，完全依賴 AI 判斷
- 更詳細資訊請查看 [審核系統更新文檔](docs/updates/direct_ai_judgment.md)

### 內容審核系統更新 (2023-07-10)
- 移除黑名單檢查機制，改為完全依賴 OpenAI 的審核 API 和 LLM 審核
- 更詳細資訊請查看 [內容審核系統更新文檔](docs/updates/moderation_system_update.md)

## 功能概述

### 聊天與互動
- AI 聊天功能：機器人能夠理解並回應用戶的消息
- 提及響應：當用戶提及機器人時，它會回應
- 隨機回覆：有機率自動回覆頻道中的消息
- 流式響應：AI 回復會分段展示，模擬真實打字

### 社區管理
- 歡迎新成員：自動歡迎加入伺服器的新成員
- 內容審核：自動檢測並處理不適當的內容
- URL 安全檢查：檢測並攔截不安全的網址，包括高效短網址追蹤和多重重定向檢查
- URL 短網址展開：自動展開短網址以顯示真實目標，防止釣魚和惡意連結
- URL 黑名單系統：自動記錄並快速識別已知的危險URL，減少API調用並提升響應速度
- 使用者超時：使用 Discord 內建超時功能禁言使用者
- 違規處理：根據違規程度自動管理用戶禁言時間

### 生產力工具
- 提醒功能：設置並發送定時提醒
- 問題管理：專門的問題頻道和解決流程
- 知識庫整合：連接 Notion 知識庫回答常見問題
- 請假系統：管理用戶請假和自動提醒

### 社區互動
- 自定義邀請：創建和管理邀請連結
- Crazy Talk 指令：工作人員可使用特殊風格回答問題

## 安裝與設置

### 環境要求
- Python 3.8+
- Discord.py 2.0+
- 其他依賴詳見 requirements.txt

### 配置文件
1. 複製 `.env.example` 到 `.env`
2. 填寫必要的設置，包括 Discord 令牌和 AI 服務配置

### 啟動機器人
```bash
python main.py
```

## 使用指南

### 基本指令
- `!help` - 顯示幫助信息
- `!crazy` - Crazy Talk 風格回答（僅限工作人員）

### 工作人員指令
- `/create_invite` - 創建永久邀請連結
- `/list_invites` - 查看邀請連結統計
- `/delete_invite` - 刪除邀請連結

## 開發資源

### 文檔
- [設置指南](docs/setup.md)
- [配置參考](docs/configuration.md)
- [API 文檔](docs/api.md)
- [更新記錄](docs/updates/)
- [基本使用教學](docs/usage.md)
- [常見問題解答](docs/faq.md)
- [指令列表](docs/commands.md)
- [內容審核](docs/content_moderation.md)
- [社群規範](docs/community_guidelines.md)
- [文化感知審核](docs/updates/culture_aware_moderation.md)
- [審核標準放寬](docs/updates/relaxed_moderation_policy.md)
- [通知順序優化](docs/updates/notification_sequence_update.md)
- [通知內容簡化](docs/updates/simplified_notification_content.md)
- [違規追蹤優化](docs/updates/violation_tracking.md)
- [API 參考文檔](docs/api.md)
- [內容審核](docs/content_moderation.md)
- [社群規範](docs/community_guidelines.md)
- [URL展開功能](docs/url_unshortening.md)
- [URL黑名單系統](docs/url_blacklist.md)
- [短網址黑名單增強](docs/updates/shortened_url_blacklist_update.md)
- [文化感知審核](docs/updates/culture_aware_moderation.md)

### 貢獻
歡迎提交 Issues 和 Pull Requests。請確保您的代碼符合項目的風格指南和質量標準。

## 功能特點

- 自動歡迎新成員
- 提醒事項管理
- 請假管理
- 邀請連結管理
- 問題追蹤系統
- FAQ 自動回應（整合 Notion）
- 自動同步斜線命令（Slash Commands）
- 增強的內容審核系統（含分級禁言）
- URL 安全檢查（檢測釣魚、詐騙和惡意連結）
- URL 短網址展開與黑名單系統（高效識別已知危險短網址）

## 環境要求

- Python 3.8+
- Discord Bot Token
- Azure OpenAI API 密鑰（用於主要 AI 功能）
- Google Gemini API 密鑰（用於分類功能）
- Notion API 密鑰（用於 FAQ 功能）

## 安裝步驟

1. 克隆專案
2. 安裝依賴：`pip install -r requirements.txt`
3. 複製 `.env.example` 到 `.env` 並填寫必要的配置
4. 設置 Notion FAQ（參見 `docs/notion_faq_setup.md`）
5. 運行機器人：`python main.py`

## 配置說明

### 基本配置

在 `.env` 文件中配置以下內容：

```env
# Discord Bot Token
DISCORD_TOKEN=your_token_here

# AI Configuration
PRIMARY_AI_SERVICE=azureopenai
PRIMARY_MODEL=gpt-4
CLASSIFIER_AI_SERVICE=gemini
CLASSIFIER_MODEL=gemini-pro

# Notion Configuration
NOTION_API_KEY=your_notion_api_key_here
NOTION_FAQ_PAGE_ID=your_faq_page_id_here
NOTION_FAQ_CHECK_ENABLED=True
```

### 功能配置

- 問題頻道：設置 `QUESTION_CHANNEL_ID`
- 請假權限：設置 `LEAVE_ALLOWED_ROLES`
- 邀請管理：設置 `INVITE_ALLOWED_ROLES`

## 功能說明

### FAQ 自動回應

當用戶在問題頻道發問時，機器人會：

1. 自動檢查是否與現有 FAQ 匹配
2. 如果找到匹配的 FAQ，立即回覆答案
3. 如果沒有匹配的 FAQ，創建討論串等待回應

詳細設置說明請參考 `docs/notion_faq_setup.md`

## 文件結構

```
.
├── app/
│   ├── ai/
│   ├── services/
│   │   └── notion_faq.py
│   ├── config.py
│   └── ...
├── docs/
│   └── notion_faq_setup.md
├── .env
├── .env.example
├── requirements.txt
└── README.md
```

## 貢獻指南

1. Fork 專案
2. 創建功能分支
3. 提交更改
4. 發起 Pull Request

## 授權

MIT License 

## 內容審核功能

HackIt Discord Bot 支援使用 OpenAI 的 omni-moderation-latest 模型進行內容審核。此功能可以檢測並移除包含不適當內容的消息和圖片。

主要特點：
- 自動審核所有消息內容和圖片
- 自動刪除違規內容
- 向使用者發送通知（頻道臨時消息和私信）
- 分級禁言機制（5分鐘/12小時/7天/7天/28天）
- 支援角色豁免機制
- URL 安全檢查（檢測釣魚、詐騙和惡意連結）
- URL 短網址展開與黑名單系統（即時識別已知危險連結，無需重複檢查）
- 完全依賴 AI 判斷，無預設白名單或黑名單

[查看詳細文檔](docs/content_moderation.md)

### 增強的內容審核系統

我們最新的增強版內容審核系統提供更好的使用者體驗和自動化禁言處理：

- 精美的UI設計，清晰呈現違規資訊
- 分級禁言機制（5分鐘/12小時/7天/7天/28天）
- 完整的社群規範，基於OpenAI的內容政策
- 禁言期滿後自動恢復使用者權限
- 支援所有OpenAI審核API返回的違規類型（包括下劃線格式）
- 優化禁言處理流程，確保刪除訊息後立即禁言
- 智能審核複查系統，避免歌曲名稱等文化內容被誤判為違規
- 嚴重違規內容快速識別，自動跳過複雜評估過程以提高處理效率
- 審核隊列系統，自動排隊處理大量消息，避免因API負載限制而漏審
- URL 安全檢查，使用 VirusTotal 或 Google Safe Browsing API 識別並阻止惡意連結的分享

[查看增強版審核功能文檔](docs/enhanced_moderation.md) | [查看社群規範](docs/community_guidelines.md) | [最新更新: 違規類別對應](docs/updates/category_mapping_update.md) | [系統修復](docs/updates/moderation_fixes.md) | [審核複查系統](docs/updates/moderation_review.md) | [誤判處理優化](docs/updates/moderation_improvements.md) | [審核隊列系統](docs/updates/moderation_queue.md) | [URL 安全檢查](docs/updates/url_safety_check.md) | [URL安全檢查修復](docs/updates/url_safety_bug_fixes.md) | [URL重定向處理改進](docs/updates/url_safety_improvements_redirects.md) | [圖片審核改進](docs/updates/image_moderation_improvements.md) | [日誌系統修復](docs/updates/logging_fixes.md) | [通知機制優化](docs/updates/moderation_update.md) | [文化感知審核](docs/updates/culture_aware_moderation.md) | [審核標準放寬](docs/updates/relaxed_moderation_policy.md) | [移除預設白名單](docs/updates/direct_ai_judgment.md) | [永久禁言修復](docs/updates/permanent_ban_fix.md)

## 安全與審核

- [AI輔助審核](docs/content_moderation.md) - AI和規則結合的內容審核系統
- [文化感知審核](docs/updates/culture_aware_moderation.md) - 支援台灣口語表達的審核系統
- [審核標準放寬](docs/updates/relaxed_moderation_policy.md) - 更寬鬆的內容審核政策
- [禁言時間修改](docs/updates/mute_duration_update.md) - 更新的違規禁言時間
- [審核通知簡化](docs/updates/simplified_moderation_notification.md) - 簡化審核結果的通知格式 

### 機器人指令
- `!crazy [內容]` - 調用無限制的回應模式

### 權限配置
- 邀請創建權限：設置 `INVITE_ALLOWED_ROLES`
- 問題解決權限：設置 `QUESTION_RESOLVER_ROLES`
- 審核豁免：設置 `CONTENT_MODERATION_BYPASS_ROLES` 