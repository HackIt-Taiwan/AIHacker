# 日誌系統改進

## 問題描述

在 Windows 環境下運行機器人時，發現日誌系統在記錄含有非 ASCII 字符（如中文字符或特殊符號）的日誌時出現編碼錯誤：

```
UnicodeEncodeError: 'charmap' codec can't encode characters in position 50-55: character maps to <undefined>
```

這個問題主要出現在 URL 安全檢查功能的日誌記錄中，特別是當用戶名包含非 ASCII 字符時。

## 改進措施

### 1. 日誌系統編碼改進

- 配置文件處理器使用 UTF-8 編碼，確保所有字符都能正確寫入日誌文件：
  ```python
  logging.FileHandler("discord_bot.log", encoding='utf-8')
  ```

- 為控制台輸出添加編碼錯誤處理：
  ```python
  class EncodingFilter(logging.Filter):
      def filter(self, record):
          try:
              # 嘗試格式化記錄，捕獲編碼錯誤
              record.getMessage()
              return True
          except UnicodeEncodeError:
              # 如果有編碼錯誤，替換有問題的字符
              record.msg = record.msg.encode('cp1252', errors='replace').decode('cp1252')
              record.args = tuple(
                  arg.encode('cp1252', errors='replace').decode('cp1252') 
                  if isinstance(arg, str) else arg 
                  for arg in record.args
              )
              return True
  ```

### 2. URL 安全檢查日誌處理增強

- 改進詳細 URL 日誌記錄，添加錯誤處理機制：
  ```python
  try:
      # 日誌記錄代碼
  except Exception as log_error:
      # 後備日誌記錄，確保即使主要日誌失敗也能記錄基本信息
      print(f"URL detail logging error: {str(log_error)}")
      logger.info("URL安全檢查結果記錄失敗")
  ```

- 安全地處理字符串連接和格式化：
  ```python
  # 安全地連接威脅類型
  threat_types_text = ""
  try:
      threat_types_text = ', '.join(threat_types)
  except Exception:
      threat_types_text = "[格式化錯誤]"
  ```

### 3. 安全的列表和字典操作

- 在訪問列表和字典之前檢查它們是否存在和非空：
  ```python
  url_count = len(urls) if urls else 0
  unsafe_count = len(unsafe_urls) if unsafe_urls else 0
  ```

## 效果

這些改進措施確保了：

1. 所有日誌都能正確記錄，無論包含什麼字符
2. 即使在出現問題時，系統仍能記錄基本的安全信息
3. 控制台輸出不會因編碼問題而中斷程序執行
4. 提高了系統在處理國際化內容時的穩定性

## 相關組件

- `main.py` - 主要日誌配置和 URL 安全檢查功能
- `logging` 模組 - Python 標準庫的日誌模組

## 注意事項

- 此修復主要針對 Windows 環境中的 cp1252 編碼問題
- 在 Linux 或 macOS 環境中，通常默認使用 UTF-8 編碼，可能不會出現這個問題
- 若在其他系統或環境中仍有類似問題，可能需要調整編碼設置 