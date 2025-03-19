# Update Notes: Bot Slash Command Synchronization and Bug Fixes

## Overview

This update adds automatic synchronization of slash commands during bot startup and fixes two critical bugs related to datetime comparisons and initialization order.

## Changes

### API and Backend Changes

1. **Automatic Command Synchronization**
   - Added code in the `on_ready` event to sync slash commands with Discord
   - Bot now logs the number of successfully synced commands during startup

2. **Bug Fixes**
   - Fixed timezone comparison error in FAQ processing by ensuring both datetime objects are timezone-aware
   - Fixed initialization order issue by initializing the leave manager before the AI handler
   - Added safety check in leave announcement updater to prevent errors when leave manager is not initialized

### Documentation Updates

1. **New Documentation**
   - Added new documentation in `docs/slash_commands.md` detailing available slash commands and how synchronization works
   
2. **README Updates**
   - Added "自動同步斜線命令（Slash Commands）" to the features list in the README

## Implementation Details

No changes to API endpoints or request/response formats were made. This update focuses on improving the bot's startup process by ensuring that all slash commands are properly registered with Discord and fixing critical bugs.

## How to Use

No action is required from users or developers. The bot will automatically sync slash commands when it starts up.

To verify that commands are properly synced:

1. Check the bot's startup logs for the message "Synced X command(s)"
2. Verify that slash commands are available in the Discord client by typing "/"

## Additional Notes

If you're developing new slash commands, they will be automatically synced when the bot restarts. There's no need for manual command registration.

# 更新說明文件

## 2024-06-20 更新：使用 Discord 內建超時功能

### 變更概述

我們已經更新了機器人的禁言系統，從基於角色的禁言機制轉換為使用 Discord 內建的超時（Timeout）功能。這一變更帶來了更好的使用體驗和更可靠的禁言管理。

### 系統變更

1. 新增兩個斜線命令：
   - `/timeout` - 對使用者設置超時
   - `/remove_timeout` - 移除使用者的超時狀態

2. 更新了 `MuteManager` 類別：
   - 新增 `timeout_user` 方法使用 Discord 的內建超時功能
   - 更新 `mute_user` 方法使用新的超時功能而非角色
   - 保留了舊版角色禁言的功能以維持向後兼容

3. 新增了管理命令 Cog：
   - 添加了 `app/moderation/mod_commands.py` 文件
   - 實現了超時相關的命令

### 使用說明

詳細的使用說明請參考 [管理工具使用指南](moderation.md)。

### 開發者影響

對於開發者，此更新有以下影響：

1. **API 變更**：
   - `MuteManager.mute_user()` 內部實現已更改為使用 Discord 的 timeout 功能，但 API 簽名保持一致
   - 新增了 `MuteManager.timeout_user()` 方法

2. **權限需求**：
   - 機器人現在需要 `moderate_members` 權限才能使用超時功能

3. **向後兼容性**：
   - 舊版禁言功能仍然可用，但將逐漸被棄用
   - 舊的禁言記錄仍然有效

### 注意事項

- Discord 的超時功能有 28 天的最大時限
- 使用者被超時後，在所有頻道都無法發言或互動
- 超時狀態會在使用者個人資料上顯示明確標記

## 先前更新

// ... 其他更新記錄 ... 