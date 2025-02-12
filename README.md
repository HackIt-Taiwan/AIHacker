# Discord Bot

## 功能特點

- 自動歡迎新成員
- 提醒事項管理
- 請假管理
- 邀請連結管理
- 問題追蹤系統
- FAQ 自動回應（整合 Notion）

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