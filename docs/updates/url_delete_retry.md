# URL安全檢查消息刪除優化

## 問題背景

在高流量的Discord伺服器中，機器人可能會遇到Discord API的速率限制（rate limit），尤其是在刪除多個消息時。這會導致一些包含不安全URL的消息刪除操作失敗，從而使這些危險連結仍然可見。

錯誤示例：
```
2025-03-26 04:19:27,483 - discord.http - WARNING - We are being rate limited. DELETE https://discord.com/api/v10/channels/1353837175355211917/messages/1354187659505041540 responded with 429. Retrying in 0.73 seconds.
```

## 解決方案

我們實現了兩項關鍵改進以解決此問題：

1. **安全刪除機制**：使用指數退避（exponential backoff）重試機制的安全消息刪除函數，確保在遇到Discord API速率限制時能夠可靠地刪除消息。

2. **即時黑名單檢查**：消息接收時立即檢查URL是否在黑名單中，不等待審核隊列處理。如果檢測到危險URL，立即刪除消息。

## 具體改進

### 安全刪除函數

新增了`safe_delete_message`函數，具有以下特點：

* 支持最多5次重試（可配置）
* 使用指數退避算法增加重試間隔
* 重試間隔上限為10秒
* 適當處理各種Discord API錯誤
* 詳細的日誌記錄

```python
async def safe_delete_message(message, reason=None):
    """安全地刪除消息，使用指數退避重試機制處理Discord的速率限制"""
    for attempt in range(1, DELETE_MESSAGE_MAX_RETRIES + 1):
        try:
            await message.delete(reason=reason)
            # 成功刪除
            return True
        except discord.errors.HTTPException as e:
            if e.status == 429:  # 速率限制
                retry_after = e.retry_after if hasattr(e, 'retry_after') else DELETE_MESSAGE_BASE_DELAY * (2 ** (attempt - 1))
                retry_after = min(retry_after, DELETE_MESSAGE_MAX_DELAY)
                logger.warning(f"刪除消息時遇到速率限制，將在 {retry_after:.2f} 秒後重試")
                await asyncio.sleep(retry_after)
            # 處理其他錯誤...
    return False
```

### 即時黑名單檢查

新增了`check_urls_immediately`函數，具有以下特點：

* 在消息處理的最早階段檢查URLs
* 只檢查是否在黑名單中，不進行完整的安全檢查
* 使用安全刪除機制移除危險消息
* 發送臨時通知告知用戶刪除原因

該函數被整合到`on_message`和`on_message_edit`事件處理程序中，確保在任何其他處理前檢查URLs。

## 配置參數

以下參數可在main.py中配置：

```python
# 刪除消息相關配置
DELETE_MESSAGE_MAX_RETRIES = 5      # 最大重試次數
DELETE_MESSAGE_BASE_DELAY = 1.0     # 基本重試延遲（秒）
DELETE_MESSAGE_MAX_DELAY = 10.0     # 最大重試延遲（秒）
```

## 效果

* **提高可靠性**：即使在高流量環境下也能可靠地刪除危險消息
* **減少失敗**：通過智能重試減少因速率限制導致的操作失敗
* **更快響應**：危險URLs在消息處理的最早階段被攔截
* **更好的用戶體驗**：用戶收到清晰的通知，解釋為什麼消息被刪除 