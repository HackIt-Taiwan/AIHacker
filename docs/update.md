# 更新說明：內容審核功能

## 概述

此次更新為 HackIt Discord Bot 新增了內容審核功能，使用 OpenAI 官方 API 的 omni-moderation-latest 模型自動檢測並過濾不適當的消息內容（包括文字和圖片）。現在支援對編輯過的消息進行審核，並採用雙重通知機制，在頻道中發送臨時通知，同時向違規用戶發送詳細的私信。

## 功能說明

當用戶發送或編輯消息時，系統將自動：
1. 審核消息中的文字內容
2. 審核消息中的圖片內容（如有）
3. 對違規內容執行自動刪除
4. 在頻道中發送臨時通知（10秒後自動刪除）
5. 透過私信向違規用戶發送詳細通知

## 配置項

以下是新增的環境變數配置：

```
# OpenAI API Configuration
OPENAI_API_KEY=sk-your_openai_api_key_here

# Content Moderation Configuration
CONTENT_MODERATION_ENABLED=True  # 設為 False 可禁用審核功能
CONTENT_MODERATION_NOTIFICATION_TIMEOUT=10  # 頻道通知顯示時間（秒）
CONTENT_MODERATION_BYPASS_ROLES=1314456999936917535  # 可繞過審核的角色 ID
```

## 技術細節

### 消息審核流程

1. 當用戶發送消息時，`on_message` 事件觸發
2. 當用戶編輯消息時，`on_message_edit` 事件觸發
3. 系統檢查消息的文字內容和附加的圖片
4. 通過 OpenAI 的 moderation API 對內容進行審核
5. 如果內容被標記為違規：
   - 自動刪除該消息
   - 在頻道中發送一條臨時通知，指明是針對特定用戶的
   - 向該用戶發送詳細的私信，說明違規原因

### API 實現

新增/修改了以下文件和功能：

- `app/ai/service/moderation.py`: 實現與 OpenAI API 的交互
- 在 `main.py` 中新增了 `on_message_edit` 事件處理函數
- 改進了 `moderate_message` 函數，支援編輯消息審核和頻道臨時通知

### 通知機制變更

- 在消息所在頻道發送臨時通知，指明是針對違規用戶的，10秒後自動刪除
- 私信中添加了頻道名稱信息，幫助用戶確認違規發生的位置
- 根據消息是新發送還是編輯，通知會顯示相應的行為類型

### 結果格式

違規檢測結果包含以下信息：
- `flagged`: 是否被標記為違規（布爾值）
- `categories`: 違規類別（如 violence, hate, sexual 等）
- `category_scores`: 每個類別的違規概率分數

## 使用示例

當用戶發送違規消息時：

1. 消息將被自動刪除
2. 用戶會在頻道中看到一條臨時通知（10秒後自動刪除）：
   ```
   ⚠️ 內容審核通知
   @用戶名 您的訊息已被系統移除，因為它含有違反社群規範的內容。
   詳細資訊已通過私訊發送給您。
   
   此訊息僅 用戶名 可見，將在 10 秒後自動刪除
   ```
3. 用戶會收到一條私信，包含詳細的違規信息：
   ```
   內容審核通知
   您在 服務器名稱 發送的訊息因含有不適當內容而被移除。

   違規類型
   violence, sexual

   頻道
   #general

   訊息內容
   [用戶的原始訊息]

   附件
   包含 1 張圖片

   請注意
   請確保您發送的內容符合社群規範。重複違規可能導致更嚴重的處罰。
   ```

## 注意事項

1. 工作人員可以通過 `CONTENT_MODERATION_BYPASS_ROLES` 配置項指定可繞過審核的角色
2. 審核功能可以通過設置 `CONTENT_MODERATION_ENABLED=False` 完全禁用
3. 只有公開消息會被審核，私信消息不會被處理
4. 新發送和編輯的消息都將得到審核
5. 頻道通知顯示時間可通過 `CONTENT_MODERATION_NOTIFICATION_TIMEOUT` 設置（默認10秒） 