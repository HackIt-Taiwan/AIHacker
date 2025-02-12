# Notion FAQ 整合設置指南

本文檔將指導你如何設置 Notion FAQ 整合功能。

## 1. 創建 Notion Integration

1. 訪問 [Notion Integrations](https://www.notion.so/my-integrations)
2. 點擊 "New integration"
3. 填寫以下資訊：
   - Name: FAQ Bot（或其他你想要的名稱）
   - Associated workspace: 選擇你要使用的工作區
4. 點擊 "Submit" 創建整合
5. 保存顯示的 "Internal Integration Token"，這將是你的 `NOTION_API_KEY`

## 2. 創建 FAQ 數據庫

1. 在 Notion 中創建一個新頁面
2. 點擊 "+ New database"
3. 選擇 "Table" 類型
4. 添加以下屬性（列）：
   - Question (Title 類型)
   - Answer (Text 類型)
   - Category (Select 類型)
   - Tags (Multi-select 類型)
5. 點擊右上角的 "Share" 按鈕
6. 在彈出的選單中找到你剛創建的整合（FAQ Bot）
7. 點擊 "Invite" 將整合添加到數據庫
8. 複製數據庫的 URL，從中提取 page_id（URL 中最後一段的 32 個字符）

## 3. 配置環境變數

在 `.env` 文件中添加以下配置：

```env
NOTION_API_KEY=your_notion_api_key_here
NOTION_FAQ_PAGE_ID=your_faq_page_id_here
NOTION_FAQ_CHECK_ENABLED=True
```

## 4. 添加 FAQ 內容

1. 在 Notion 數據庫中，每行代表一個 FAQ 條目
2. 填寫以下欄位：
   - Question: FAQ 問題
   - Answer: 詳細答案
   - Category: FAQ 分類（可選）
   - Tags: 相關標籤（可選）

## 5. 功能說明

當用戶在指定的問題頻道發問時，機器人會：

1. 自動檢查問題是否與現有 FAQ 匹配
2. 如果找到匹配的 FAQ：
   - 立即回覆包含 FAQ 答案的嵌入訊息
   - 顯示問題分類和標籤（如果有）
3. 如果沒有找到匹配的 FAQ：
   - 創建討論串等待工作人員回應
   - 添加解決按鈕

## 6. 維護建議

1. 定期更新 FAQ 內容
2. 確保答案清晰完整
3. 適當使用分類和標籤以便於管理
4. 定期檢查 API 密鑰的有效性

## 7. 故障排除

如果遇到問題：

1. 確認 API 密鑰正確且有效
2. 檢查數據庫 ID 是否正確
3. 確保整合已被正確添加到數據庫
4. 檢查日誌中的錯誤訊息

## 8. 安全注意事項

1. 永遠不要公開分享你的 API 密鑰
2. 定期更換 API 密鑰
3. 限制數據庫的訪問權限
4. 定期審查整合的權限設置 