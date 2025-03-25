# 黑名單URL懲罰系統更新

## 更新概述

我們增強了黑名單URL檢測系統，使其在發現用戶發送了黑名單中的URL時，不僅能夠刪除消息，還會對用戶進行適當的處罰和提醒，就像常規內容審核系統一樣。

## 問題背景

在之前的實現中，當用戶發送包含黑名單URL的消息時，系統會：
1. 立即刪除包含危險URL的消息
2. 在頻道中發送一個簡短的臨時通知

但是，這種處理方式有以下不足：
1. 不記錄用戶的違規行為
2. 不對重複違規的用戶實施禁言等懲罰措施
3. 不向用戶發送詳細的DM通知，讓他們了解為什麼內容被刪除
4. 處理方式與正常內容審核流程不一致，導致管理體驗不統一

## 更新內容

我們對`check_urls_immediately`函數進行了全面升級，使其處理方式與標準內容審核流程保持一致：

1. **完整的懲罰機制**：
   - 記錄違規行為到用戶的違規歷史中
   - 根據配置的禁言策略對重複違規用戶進行禁言
   - 處理方式與一般違規內容完全相同

2. **詳細的通知系統**：
   - 在頻道中發送暫時的違規通知
   - 向用戶DM發送詳細的違規報告，包括：
     - 具體的違規URL列表
     - 威脅類型（釣魚、惡意軟體等）
     - 違規計數（第幾次違規）
     - 頻道信息
     - 原始消息內容
     - 社群規範指引

3. **重複違規保護**：
   - 檢測用戶是否在短時間內重複違規
   - 對於連續違規的用戶，僅刪除消息而不重複發送大量通知

4. **詳細的日誌記錄**：
   - 記錄所有處理行為到日誌系統
   - 包括URL檢測、禁言操作和通知發送的詳細信息

## 行為變更

用戶發送黑名單URL時的新處理流程：

1. 消息被立即刪除
2. 頻道內發送一條簡短的通知訊息（10秒後自動刪除）
3. 向用戶發送一條私信詳細說明違規原因和處罰
4. 違規計入用戶的違規歷史
5. 根據用戶的違規記錄和配置的禁言策略，可能會對用戶實施禁言
6. 如果實施禁言，會額外向用戶發送一條禁言通知私信

## 預期效果

1. **一致的管理體驗**：無論是黑名單URL還是其他違規內容，處理方式都保持一致
2. **更好的用戶教育**：用戶收到詳細通知，了解為什麼內容被刪除，有助於防止再次違規
3. **更有效的處罰機制**：重複發送危險URL的用戶將面臨累進式的處罰
4. **管理效率提高**：自動處理整個流程，無需管理員額外介入

## 技術實現

核心更改在`check_urls_immediately`函數中，我們將其與`moderate_message`函數的處理流程對齊：

```python
# 創建URL檢查結果用於禁言系統
url_check_result = {
    "is_unsafe": True,
    "unsafe_urls": blacklisted_urls,
    "threat_types": list(threat_types),
    "severity": max_severity,
    "results": blacklist_results
}

# 創建違規類別列表
violation_categories = []
for threat_type in threat_types:
    violation_category = threat_type.lower()
    if violation_category not in violation_categories:
        violation_categories.append(violation_category)

# 應用禁言（如果已配置禁言管理器）
if mute_manager:
    mute_success, mute_reason, mute_embed = await mute_manager.mute_user(
        user=author,
        violation_categories=violation_categories,
        content=text,
        details={"url_safety": url_check_result}
    )
```

## 下一步計劃

1. 進一步優化黑名單URL的檢測邏輯，提高準確性
2. 考慮添加不同級別的處罰，基於URL威脅的嚴重程度
3. 為管理員添加查看黑名單URL違規統計的命令 