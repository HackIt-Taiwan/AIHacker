# URL安全檢查系統

## 功能概述

URL安全檢查系統是Discord機器人的關鍵安全功能，專門用於識別和阻止惡意連結、釣魚網站和詐騙嘗試。該系統採用多層檢測方法，能夠攔截各種嘗試規避標準安全措施的惡意連結。

## 主要功能

### 域名仿冒和釣魚檢測

- **仿冒(Typosquatting)檢測**：識別嘗試模仿流行網站的域名
  - 例如：`steamcommunuttly.com` 而非正常的 `steamcommunity.com`
  - 支持檢測超過15種流行平台的仿冒，包括Steam、Discord、Roblox等
  
- **路徑關鍵詞分析**：識別URL路徑中的可疑關鍵詞
  - 檢測常見於釣魚攻擊的詞彙如 "gift"、"free"、"activation"、"login" 等
  - 識別混合戰術，如正常域名但使用可疑子路徑的情況

- **已知釣魚域名黑名單**：維護已知詐騙域名資料庫

### 重定向追蹤

- **短網址解析**：自動展開短網址(bit.ly、tinyurl等)以檢查其真實目的地
- **多層重定向處理**：可以追蹤最多5層的重定向鏈，確保無法通過多重跳轉來規避檢測
- **重定向安全評估**：標記重定向到不安全網站的所有原始連結

### 第三方API整合

- **VirusTotal整合**：使用全球最大的威脅情報數據庫之一進行URL分析
- **Google Safe Browsing整合**：檢測已知的惡意網站和釣魚域名
- **重試和備用邏輯**：處理API限制和服務中斷

### 保守處理機制

- **不完整分析處理**：當API分析未完成時，保守判斷機制會基於其他因素作出決策
- **可疑指標累積**：結合多個可疑因素（短網址+可疑關鍵詞）提高檢測準確性
- **品牌保護**：特別關注涉及遊戲、社交媒體等常見釣魚目標的URL

## 配置選項

系統可通過以下環境變量進行自定義配置：

```
# 基本配置
URL_SAFETY_CHECK_ENABLED=True
URL_SAFETY_CHECK_API=virustotal
URL_SAFETY_API_KEY=your_api_key_here
URL_SAFETY_THRESHOLD=0.3

# 高級配置
URL_SAFETY_MAX_RETRIES=3
URL_SAFETY_RETRY_DELAY=2
URL_SAFETY_REQUEST_TIMEOUT=5.0
URL_SAFETY_IMPERSONATION_DOMAINS=steamcommunuttly,discord-gift,discordnitro
```

## 實際應用場景

### 阻止Steam釣魚嘗試

以下是一個真實的釣魚攻擊示例：

1. 使用者分享短網址：`https://shorturl.at/ruo7Y`
2. 系統解析後發現它重定向到：`https://steamcommunuttly.com/gift/activation=Dor5Fhnm2w`
3. 系統識別出多個可疑因素：
   - 域名使用了"communuttly"而非正確的"community"
   - URL路徑包含"gift"和"activation"這些釣魚關鍵詞
   - 整體模式符合Steam禮品卡詐騙
4. 系統自動刪除訊息並記錄詳細的檢測原因

### 識別新型釣魚網站

即使是新創建的釣魚網站（尚未被安全資料庫收錄）也能被檢測到：

1. 使用者發送一個重定向到新釣魚網站的連結
2. VirusTotal返回"queued"狀態（尚未完成分析）
3. 系統進行額外的域名和路徑分析
4. 基於域名模式、路徑關鍵詞和連結結構，將其標記為可疑
5. 在日誌中記錄具體的檢測原因

## 系統優勢

- **多層檢測**：結合API查詢、域名分析和路徑檢測
- **實時解析**：即時展開短網址和追蹤重定向
- **高適應性**：即使遇到API限制或新型威脅也能有效運作
- **詳細日誌**：提供完整的檢測原因和決策依據
- **可配置性**：可根據需求調整敏感度和檢測策略

---

此系統設計用於主動預防社區成員遭受釣魚和詐騙嘗試，特別關注遊戲相關詐騙，如假Steam禮品卡、Discord Nitro騙局和免費遊戲幣騙局等，這些是Discord社區中最常見的詐騙類型。 