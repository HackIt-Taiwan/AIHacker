# Discord Bot

## 功能特點

- 自動歡迎新成員
- 提醒事項管理
- 請假管理
- 邀請連結管理
- 問題追蹤系統
- FAQ 自動回應（整合 Notion）
- 自動同步斜線命令（Slash Commands）
- 增強的內容審核系統（含分級禁言）

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
- 分級禁言系統（違規次數累計增加禁言時間）
- 支援角色豁免機制

[查看詳細文檔](docs/content_moderation.md)

### 增強的內容審核系統

我們最新的增強版內容審核系統提供更好的使用者體驗和自動化禁言處理：

- 精美的UI設計，清晰呈現違規資訊
- 分級禁言機制（5分鐘/12小時/7天/30天/1年）
- 完整的社群規範，基於OpenAI的內容政策
- 禁言期滿後自動恢復使用者權限
- 支援所有OpenAI審核API返回的違規類型（包括下劃線格式）
- 優化禁言處理流程，確保刪除訊息後立即禁言
- 智能審核複查系統，避免歌曲名稱等文化內容被誤判為違規
- 嚴重違規內容快速識別，自動跳過複雜評估過程以提高處理效率
- 審核隊列系統，自動排隊處理大量消息，避免因API負載限制而漏審

[查看增強版審核功能文檔](docs/enhanced_moderation.md) | [查看社群規範](docs/community_guidelines.md) | [最新更新: 違規類別對應](docs/updates/category_mapping_update.md) | [系統修復](docs/updates/moderation_fixes.md) | [審核複查系統](docs/updates/moderation_review.md) | [誤判處理優化](docs/updates/moderation_improvements.md) | [審核隊列系統](docs/updates/moderation_queue.md) 