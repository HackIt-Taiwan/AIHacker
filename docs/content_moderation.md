# 內容審核功能

HackIt Discord Bot 現在支援使用 OpenAI 的 omni-moderation-latest 模型進行內容審核。此功能可以檢測並移除包含不適當內容的消息和圖片。

## 功能特點

- 使用 OpenAI 官方 API 的 omni-moderation-latest 模型進行審核
- 支援審核文字內容
- 支援審核圖片內容
- 支援審核編輯過的消息
- 對違規內容進行自動刪除
- 在頻道中發送臨時通知（10秒後自動刪除）
- 向違規用戶發送詳細的私信通知
- 支援角色豁免機制

## 配置說明

在 `.env` 文件中可以對內容審核功能進行配置：

```
# OpenAI API 配置
OPENAI_API_KEY=sk-your_openai_api_key_here

# 內容審核配置
CONTENT_MODERATION_ENABLED=True  # 是否啟用內容審核
CONTENT_MODERATION_NOTIFICATION_TIMEOUT=10  # 頻道通知消息的顯示時間（秒）
CONTENT_MODERATION_BYPASS_ROLES=1234567890,9876543210  # 可繞過審核的角色 ID，用逗號分隔
```

## 工作原理

1. 當使用者發送消息或編輯現有消息時，系統檢查消息的文字內容和附加的圖片
2. 使用 OpenAI 的 omni-moderation-latest 模型對內容進行審核
3. 如果內容被標記為違規（包括但不限於暴力、性、仇恨言論等類型）：
   - 自動刪除該消息
   - 在頻道中發送一條臨時通知，指明是針對特定用戶的（10秒後自動刪除）
   - 向該用戶發送詳細的私信，說明違規原因和內容

## 隱私保護

- 違規消息會被立即刪除，以保護其他社群成員
- 頻道中的通知會在短時間內自動刪除，減少對其他用戶的干擾
- 詳細的違規信息只會通過私信發送給違規用戶本人

## 輸出示例

頻道通知（10秒後自動刪除）：
```
⚠️ 內容審核通知
@用戶名 您的訊息已被系統移除，因為它含有違反社群規範的內容。
詳細資訊已通過私訊發送給您。

此訊息僅 用戶名 可見，將在 10 秒後自動刪除
```

私信通知：
```
内容審核通知
您在 服務器名稱 發送的訊息因含有不適當內容而被移除。

違規類型
violence, sexual, hate

頻道
#general

訊息內容
[用戶的原始訊息]

附件
包含 2 張圖片

請注意
請確保您發送的內容符合社群規範。重複違規可能導致更嚴重的處罰。
```

## 支援的違規類別

OpenAI 的 moderation API 能夠檢測以下類型的違規內容：

- `harassment`: 騷擾內容
- `harassment/threatening`: 威脅性騷擾
- `hate`: 仇恨言論
- `hate/threatening`: 威脅性仇恨言論
- `self-harm`: 自我傷害
- `self-harm/intent`: 自我傷害意圖
- `self-harm/instructions`: 自我傷害指導
- `sexual`: 性相關內容
- `sexual/minors`: 未成年相關性內容
- `violence`: 暴力內容
- `violence/graphic`: 圖像化暴力內容
- `illicit`: 不法行為
- `illicit/violent`: 暴力不法行為

注意：目前圖片審核僅支援部分類別（暴力、自我傷害和性相關內容），其他類別僅針對文字內容。

## 技術實現

內容審核功能主要由以下部分組成：

1. `app/ai/service/moderation.py`: 負責與 OpenAI API 交互，實現內容審核的核心邏輯
2. 在 `main.py` 中實現的事件處理：
   - `on_message`: 處理新發送的消息
   - `on_message_edit`: 處理編輯過的消息
   - `moderate_message`: 審核消息內容並處理違規情況

這個功能為維護健康的社區環境提供了重要保障，確保所有成員的交流都符合社群規範。 