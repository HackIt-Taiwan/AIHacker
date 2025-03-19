# 圖片審核系統改進

## 改進內容

### 1. 增強圖片 URL 檢測

系統現在可以檢測和審核以下類型的圖片：
- 直接上傳的圖片附件
- 消息內容中的圖片 URL
- 支援的圖片格式：PNG、JPG、JPEG、GIF、WEBP

### 2. 改進的圖片 URL 提取

```python
# 從附件中提取圖片 URL
image_urls = []
for attachment in attachments:
    if attachment.content_type and attachment.content_type.startswith('image/'):
        image_urls.append(attachment.url)

# 從消息內容中提取圖片 URL
if text:
    image_url_pattern = r'https?://[^\s<>"]+?\.(?:png|jpg|jpeg|gif|webp)'
    image_urls.extend(re.findall(image_url_pattern, text, re.IGNORECASE))
```

### 3. 審核流程

1. 收集所有圖片 URL（包括附件和消息內容中的）
2. 將所有圖片 URL 發送給 OpenAI 的內容審核 API
3. 根據審核結果採取適當的行動：
   - 如果圖片違規，刪除消息
   - 向用戶發送通知
   - 根據違規歷史決定是否實施禁言

## 系統行為

當用戶發送包含圖片的消息時，系統會：
1. 檢查消息中的所有圖片（無論是附件還是 URL）
2. 對每個圖片進行內容審核
3. 如果任何圖片被標記為違規，整個消息將被刪除
4. 用戶將收到詳細的通知，說明違規原因

## 相關組件

- `main.py` - 包含主要的內容審核邏輯
- `app/ai/service/moderation.py` - 內容審核服務
- `app/services/moderation_queue.py` - 審核隊列服務

## 注意事項

- 系統會同時檢查消息中的文字和圖片內容
- 圖片審核結果會影響整個消息的處理
- 支援的圖片格式可以通過修改正則表達式模式來擴展

---

此改進確保了所有圖片內容都經過適當的審核，提供了更全面的內容安全保護。 