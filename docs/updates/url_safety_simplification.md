# URL 安全系統簡化: 移除短網址擴展功能

## 摘要
本次更新簡化了 URL 安全模組，移除了短網址識別、擴展和自定義威脅檢測邏輯，使系統專注於使用第三方 API 進行基本的惡意網址檢測，降低系統複雜度，提高可靠性和效能。

## 變更說明

1. **移除短網址擴展功能**：
   - 移除所有擴展短網址的邏輯 (包括 URL 遞迴追蹤功能)
   - 移除短網址服務列表和特殊處理規則
   - 不再追蹤重定向連結

2. **移除自定義威脅檢測**：
   - 移除域名冒充檢測功能
   - 移除可疑路徑檢測功能
   - 移除可疑參數檢測功能
   - 移除頁面內容分析功能
   - 移除可疑域名模式檢測

3. **專注於第三方 API 檢測**：
   - 系統現在完全依賴 VirusTotal API 進行 URL 安全檢測
   - 不再進行本地啟發式分析

## API 變更

主要 API 功能保持不變，但回傳資料現已大幅簡化：

```python
{
    "url": "https://example.com/page",
    "is_unsafe": True/False,
    "check_time": "2024-07-29T12:34:56",
    "message": "External API threat detection" / "URL passed safety checks",
    "unsafe_score": 0.85,  # 如果檢測到威脅 (0-1)
    "threat_types": ["PHISHING"],  # 如果檢測到威脅
    "severity": 8,  # 如果檢測到威脅
}
```

## 技術實現

1. **URL 檢測邏輯簡化**:
   - 直接使用原始 URL 進行安全檢測
   - 不再進行短網址擴展
   - 仍保留從文本中提取 URL 的功能

2. **API 整合**:
   - 保留 VirusTotal API 檢測功能
   - 移除 Google Safe Browsing API 支援

## 改進效果

1. **降低複雜性**: 移除多層遞迴擴展和啟發式分析，降低系統複雜度
2. **減少誤判**: 移除可能導致誤判的自定義啟發式規則
3. **提高效能**: 降低多次 HTTP 請求的需求，加快檢測速度
4. **減少依賴**: 不再依賴多個外部服務或 API

## 使用範例

使用方式與之前相同，但不再提供短網址擴展功能：

```python
# 在你的應用程式中使用
from app.ai.service.url_safety import URLSafetyChecker

async def check_message_safety(message_content):
    url_checker = URLSafetyChecker()
    urls = await url_checker.extract_urls(message_content)
    if urls:
        results = await url_checker.check_urls(urls)
        # 處理安全檢查結果
        for url, result in results[1].items():
            if result.get("is_unsafe"):
                print(f"偵測到不安全的 URL: {url}")
                print(f"原因: {result.get('message')}")
        return results
    return None
```

## 總結

此更新透過移除短網址擴展和自定義威脅檢測功能，簡化了 URL 安全檢查系統。系統現在專注於使用 VirusTotal API 進行基本的 URL 安全檢測，提供更穩定和高效的威脅偵測服務。 