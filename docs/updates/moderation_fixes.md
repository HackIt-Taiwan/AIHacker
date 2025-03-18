# 內容審核系統修復更新

## 問題修復

本次更新解決了內容審核系統中的三個關鍵問題：

1. **JSON 序列化錯誤**：修復了 `Object of type Categories is not JSON serializable` 錯誤，該錯誤發生在處理 OpenAI Moderation API 返回的 Categories 對象時。

2. **禁言時序優化**：重新安排了審核流程，確保在刪除違規訊息後立即處理禁言處分，而不是在其他操作之後。

3. **SQL 語法錯誤修復**：解決了 `Error muting user: near "ORDER": syntax error` 錯誤，此錯誤導致在某些情況下無法成功禁言用戶。

## 技術修改

### 1. 新增序列化輔助函數

在 `app/ai/service/moderation.py` 中添加了 `convert_to_dict()` 函數，用於將 OpenAI API 返回的 `Categories` 和 `CategoryScores` 對象轉換為可 JSON 序列化的字典。

```python
def convert_to_dict(obj: Any) -> Union[Dict, Any]:
    """
    Convert an object to a dictionary for JSON serialization.
    Works recursively for nested objects with __dict__ attribute.
    """
    if hasattr(obj, '__dict__'):
        return {key: convert_to_dict(value) for key, value in obj.__dict__.items()}
    return obj
```

這確保了在保存違規記錄到數據庫時不會出現序列化錯誤。

### 2. 優化禁言處理順序

在 `main.py` 的 `moderate_message()` 函數中，更改了操作順序：

1. 首先刪除違規訊息
2. 然後立即處理禁言（之前位於頻道通知之後）
3. 之後處理頻道通知和 DM 通知

新增了額外的錯誤處理和日誌記錄，以便更好地追蹤禁言過程中的任何問題。

### 3. 修復 SQLite 語法錯誤

修改了 `app/moderation_db.py` 中的 `add_mute()` 方法，解決 SQLite 不支持在 UPDATE 語句中直接使用 ORDER BY 的問題：

```python
# 修改前（錯誤的寫法）
cursor.execute('''
UPDATE violations
SET muted = TRUE
WHERE user_id = ? AND guild_id = ?
ORDER BY id DESC LIMIT 1
''', (user_id, guild_id))

# 修改後（正確的寫法）
# 先獲取最新違規記錄的ID
cursor.execute('''
SELECT id FROM violations
WHERE user_id = ? AND guild_id = ?
ORDER BY id DESC LIMIT 1
''', (user_id, guild_id))

latest_violation = cursor.fetchone()
if latest_violation:
    # 然後更新該特定違規記錄
    cursor.execute('''
    UPDATE violations
    SET muted = TRUE
    WHERE id = ?
    ''', (latest_violation[0],))
```

這個修改將一個不符合 SQLite 語法的複雜查詢拆分為兩個簡單的查詢，確保了禁言操作能夠正確執行。

## 改進效果

1. **穩定性改進**：解決了因 JSON 序列化問題導致的錯誤，使審核系統更加穩定可靠。

2. **即時禁言**：確保違規用戶在訊息被刪除後立即被禁言，不會因其他操作失敗而延遲或遺漏禁言處理。

3. **更好的錯誤報告**：增強了日誌記錄，使故障排除和監控更加容易。

4. **禁言成功率提高**：修復了 SQL 語法錯誤後，所有違規用戶現在都能被正確地禁言，不再出現「禁言失敗」的情況。

## 注意事項

這些變更不會影響審核系統的外部行為或用戶體驗，僅優化了內部處理流程和穩定性。用戶仍會看到相同的通知和禁言訊息，但系統現在更可靠地執行這些操作。 