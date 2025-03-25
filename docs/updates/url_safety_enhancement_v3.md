# URL 安全增強: 進階威脅偵測系統

## 摘要
此更新顯著提升 URL 安全模組的威脅檢測功能，加入針對釣魚、惡意軟體和詐騙網站的先進啟發式分析。新功能包括頁面內容分析、可疑域名偵測、URL 參數掃描和短網址特殊處理，大幅提高對隱藏威脅的識別能力。

## 主要增強功能

1. **頁面內容啟發式分析**：
   - 登入表單偵測 (特別是非 HTTPS 網站上的表單)
   - 信用卡輸入欄位識別
   - 混淆 JavaScript 代碼偵測
   - 社交工程關鍵詞辨識
   - 品牌冒充偵測
   - 跨域表單提交分析

2. **可疑域名識別**：
   - 隨機生成域名模式識別
   - 過多子域名偵測
   - 可疑 TLD (頂級域名) 檢查
   - 字母數字交替模式識別
   - 品牌名稱混入域名偵測

3. **URL 參數分析**：
   - 可疑參數名稱偵測
   - Base64 編碼資料掃描
   - 多重可疑參數組合識別

4. **短網址特殊處理**：
   - 對短網址進行更嚴格的安全檢查
   - 未能展開的短網址標記為可疑
   - 短網址跨域重定向威脅升級
   - 短網址隱藏高威脅內容的特別偵測

5. **多層威脅評分系統**：
   - 綜合評分機制結合多種威脅指標
   - 明確的威脅原因描述
   - 詳細的內容分析報告

## 技術實現

### 內容分析邏輯

新的內容分析功能會在 URL 展開過程中獲取頁面 HTML 內容，並進行以下分析：

1. **登入表單偵測**: 檢查密碼欄位和登入表單的存在
2. **信用卡資訊輸入偵測**: 尋找信用卡號、CVV 碼、有效期等輸入欄位
3. **混淆代碼識別**: 檢測常見的 JavaScript 混淆技術
4. **表單目標分析**: 檢查表單提交目標，特別是跨域提交
5. **隱藏元素檢查**: 偵測過多的隱藏表單欄位 (釣魚網站常見特徵)
6. **社交工程詞彙分析**: 檢查頁面中的緊急、驗證、帳戶限制等關鍵詞
7. **品牌提及識別**: 檢測頁面中提及的品牌名稱，並與域名比對

### 可疑域名檢測邏輯

域名檢測功能會識別以下可疑特徵：

- 隨機生成的長數字字母組合域名
- 包含三個或更多子域名的 URL
- 使用已知的可疑 TLD (.tk, .ml, .ga 等)
- 數字和字母交替模式 (如 a1b2c3.com)
- 包含知名品牌名稱但非官方域名

### URL 參數分析

URL 參數分析會檢查：

- 包含敏感名稱的參數 (token, auth, password 等)
- 包含 Base64 編碼資料的參數值，特別是解碼後包含敏感資訊或 URL 的
- 多個可疑參數的組合使用

### API 更新

公開 API 功能保持不變，但回傳資料更加豐富：

```python
{
    "original_url": "https://shorturl.at/example",
    "expanded_url": "https://actual-destination.com/page",
    "is_unsafe": True,
    "unsafe_score": 0.85,  # 威脅評分 (0-1)
    "threat_types": ["PHISHING"],  # 威脅類型
    "severity": 8,  # 嚴重程度等級
    "reason": "Login form with multiple social engineering keywords: verify, security, account suspended",  # 詳細原因
    "content_analysis_detection": True,  # 威脅偵測來源
    "check_time": "2024-07-27T12:34:56",
    "expansion_performed": True  # 是否展開了短網址
}
```

### 流程整合

1. URL 安全檢查現在包含完整的處理流程:
   - 首先通過遞迴方式展開 URL
   - 對展開的 URL 進行域名、路徑和參數分析
   - 分析之前獲取的頁面內容
   - 使用配置的外部 API 進行額外安全檢查
   - 整合所有分析結果並提供綜合評分

2. 短網址特殊處理:
   - 對所有展開的短網址進行跨域分析
   - 對未成功展開的短網址標記為可疑
   - 為隱藏高嚴重性威脅的短網址提高威脅評分

## 改進效果

1. **更高的偵測率**: 能夠識別更多種類的威脅，包括之前可能遺漏的釣魚網站和欺詐頁面
2. **減少誤報**: 通過多重指標綜合評估，提高判斷準確性
3. **更詳細的威脅情報**: 提供明確的威脅類型和原因說明
4. **特別關注短網址**: 對短網址進行額外審查，更有效地識別隱藏威脅

## 使用範例

使用方式與之前相同，但提供更詳細的結果:

```python
# 在你的應用程式中使用
from app.ai.service.url_safety import URLSafetyService

async def check_message_safety(message_content):
    url_service = URLSafetyService()
    urls = url_service.extract_urls(message_content)
    if urls:
        results = await url_service.check_urls(urls)
        # 處理安全檢查結果並獲取詳細威脅資訊
        for url, result in results.items():
            if result.get("is_unsafe"):
                print(f"偵測到不安全的 URL: {url}")
                print(f"威脅類型: {result.get('threat_types')}")
                print(f"原因: {result.get('reason')}")
        return results
    return None
```

## 未來改進方向

1. **URL 信譽系統**: 建立 URL 和域名的本地信譽資料庫
2. **機器學習整合**: 使用 ML 模型進一步提高釣魚和惡意網站的檢測率
3. **威脅情報整合**: 接入更多外部威脅情報源
4. **內容渲染分析**: 使用無頭瀏覽器進行更深入的內容分析

## 總結

此更新顯著提升了 URL 安全檢查功能，特別是對釣魚網站和欺詐頁面的偵測能力。通過結合多層威脅分析技術，系統現在能夠更有效地識別和防範各種網路威脅，尤其是隱藏在短網址背後的惡意內容。 