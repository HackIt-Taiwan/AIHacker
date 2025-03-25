# Bug修復記錄

## IGNORED_CHANNELS未定義修復 (2024-03-27)

### 問題描述
機器人啟動後在處理消息時出現錯誤：`NameError: name 'IGNORED_CHANNELS' is not defined`，導致無法正常處理消息。

### 修復方案
在main.py中添加了空的`IGNORED_CHANNELS`列表定義：
```python
# 設置空的IGNORED_CHANNELS列表，表示不屏蔽任何頻道
IGNORED_CHANNELS = []
```

### 影響範圍
- 修復前：機器人無法正常處理任何消息，會在每條消息處理時報錯
- 修復後：機器人能夠正常處理所有頻道的消息，不會忽略任何頻道

### 相關配置
如果未來需要屏蔽特定頻道，可以在`IGNORED_CHANNELS`列表中添加頻道ID，例如：
```python
# 屏蔽特定頻道，這些頻道中的消息將不會被處理
IGNORED_CHANNELS = [11111111111111, 22222222222222]
```

## 消息刪除時的 PartialMessage 參數錯誤 (2024-03-27)

### 問題描述
在處理編輯後的消息時，系統出現以下錯誤：
```
PartialMessage.delete() got an unexpected keyword argument 'reason'
```

這個錯誤發生是因為當使用 `on_message_edit` 事件處理編輯後的消息時，Discord API 可能返回 `PartialMessage` 對象而不是完整的 `Message` 對象。`PartialMessage` 類的 `delete()` 方法不接受 `reason` 參數，導致函數調用出錯。

### 修復方法
修改了 `safe_delete_message` 函數，使其能夠識別 `PartialMessage` 對象並適當地調用其 `delete()` 方法：

```python
async def safe_delete_message(message, reason=None):
    # ... 其他代碼 ...
    try:
        # 檢查是否為PartialMessage，它不支持reason參數
        if isinstance(message, discord.PartialMessage) or message.__class__.__name__ == 'PartialMessage':
            await message.delete()
        else:
            await message.delete(reason=reason)
        # ... 其他代碼 ...
    except Exception as e:
        # ... 錯誤處理 ...
```

此修復確保了系統能夠正確處理 `Message` 和 `PartialMessage` 兩種類型的對象，無論是在正常消息處理還是編輯消息處理流程中。

## 缺少`IGNORED_CHANNELS`定義導致的消息處理錯誤 (2024-03-27)

### 問題描述
機器人在處理消息時因為在配置文件中缺少 `IGNORED_CHANNELS` 定義而出錯，導致無法正確處理某些頻道的消息。

### 修復方法
在 `config.py` 文件中添加了默認的 `IGNORED_CHANNELS` 設置：

```python
# 預設被忽略的頻道列表
IGNORED_CHANNELS = os.environ.get('IGNORED_CHANNELS', '').split(',')
IGNORED_CHANNELS = [int(channel_id) for channel_id in IGNORED_CHANNELS if channel_id.strip().isdigit()]
```

同時在 `.env` 文件中添加了相應的配置選項：

```
# 忽略的頻道ID列表，以逗號分隔
IGNORED_CHANNELS=
```

這確保了即使用戶沒有明確設置 `IGNORED_CHANNELS`，機器人也能正常工作，不會因為引用未定義的變量而出錯。 