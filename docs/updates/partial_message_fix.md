# Discord PartialMessage 刪除錯誤修復

## 問題背景

在處理編輯過的消息時，Discord API 有時會返回 `PartialMessage` 對象而不是完整的 `Message` 對象。這種情況通常發生在以下場景：

1. 編輯較舊的消息（已不在緩存中）
2. 機器人剛啟動後，編輯之前的消息
3. 某些API請求限制導致只能取得部分消息數據

`PartialMessage` 是 Message 對象的有限版本，它只包含少量的屬性和方法。特別是，其 `delete()` 方法與完整 `Message` 對象的 `delete()` 方法有所不同 - 它不接受 `reason` 參數。

## 錯誤詳情

當機器人試圖使用 `safe_delete_message` 函數刪除包含危險URL的編輯過消息時，出現以下錯誤：

```
2025-03-26 04:23:43,323 - __main__ - ERROR - 刪除消息時發生未知錯誤: PartialMessage.delete() got an unexpected keyword argument 'reason'
```

這個錯誤會導致刪除操作失敗，使危險URL繼續保留在頻道中，無法被及時移除。錯誤會重複多次（重試機制），但每次都會因為相同原因失敗。

## 技術分析

錯誤的根本原因是 `safe_delete_message` 函數在刪除消息時總是包含 `reason` 參數：

```python
await message.delete(reason=reason)
```

而當 `message` 是 `PartialMessage` 類型時，其 `delete()` 方法簽名不包含 `reason` 參數，導致參數不匹配錯誤。

## 解決方案

修改 `safe_delete_message` 函數，使其能夠識別消息對象的具體類型，並根據類型調用適當的 `delete()` 方法：

```python
async def safe_delete_message(message, reason=None):
    """
    安全地刪除消息，使用指數退避重試機制處理Discord的速率限制
    
    Args:
        message: 要刪除的Discord消息
        reason: 刪除原因（可選）
    
    Returns:
        bool: 刪除成功返回True，失敗返回False
    """
    for attempt in range(1, DELETE_MESSAGE_MAX_RETRIES + 1):
        try:
            # 檢查是否為PartialMessage，它不支持reason參數
            if isinstance(message, discord.PartialMessage) or message.__class__.__name__ == 'PartialMessage':
                await message.delete()
            else:
                await message.delete(reason=reason)
            
            # 成功刪除
            if attempt > 1:
                logger.info(f"成功刪除消息，嘗試次數: {attempt}")
            return True
        except discord.errors.HTTPException as e:
            # 重試邏輯...
```

這個修復使用了兩種方法來識別 `PartialMessage`：
1. 使用 `isinstance()` 進行直接類型檢查
2. 檢查類名 `__class__.__name__`，作為備用方法

雙重檢查確保在不同環境和Discord.py版本中都能正確識別PartialMessage對象。

## 影響與效益

1. **提高刪除可靠性**：確保所有消息（包括編輯過的）都能被正確刪除
2. **增強安全性**：危險URL會被及時移除，無論它們是在新消息還是編輯過的消息中
3. **改善錯誤處理**：避免日誌中出現大量重複錯誤

## 測試結果

修復後，系統能夠正確處理各種情況下的消息刪除：
- 新發送的消息
- 剛編輯過的消息
- 編輯較舊的（非緩存）消息

對於編輯過的消息，即使返回的是 `PartialMessage` 對象，也能成功刪除而不再出現參數錯誤。 