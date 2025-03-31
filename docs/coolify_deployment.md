# Coolify 部署指南

本文檔提供了如何使用 Coolify 部署 AIHacker Discord Bot 的詳細說明。

## Coolify 環境設置

Coolify 是一個開源的自託管 PaaS (Platform as a Service)，可以輕鬆部署 Docker 容器化應用。AIHacker Discord Bot 已經進行了優化，使其可以在 Coolify 環境中無縫運行。

### 重要注意事項

1. **環境變數處理**：Coolify 直接將環境變數注入到容器中，不需要使用 `.env` 文件
2. **資料持久化**：使用 Coolify 的卷映射功能保存資料和日誌

## 部署步驟

### 1. 在 Coolify 中建立新應用

1. 登入 Coolify 控制台
2. 選擇或建立目標項目和目標服務器
3. 點擊「+ 新資源」>「應用程序」
4. 選擇「Git Repository」並輸入 AIHacker Discord Bot 的倉庫 URL

### 2. 配置構建設置

1. 分支：選擇 `main` 或您的目標分支
2. 根目錄：留空（使用倉庫根目錄）
3. 構建方法：選擇「Dockerfile」（預設應該已選擇）
4. Docker Compose：禁用（除非您想使用 docker-compose.yml 進行部署）

### 3. 配置環境變數

在 Coolify 的「環境變數」部分，添加所有必要的變數：

```
DISCORD_TOKEN=your_token_here
PRIMARY_AI_SERVICE=azureopenai
PRIMARY_MODEL=gpt-4o
...等其他變數
```

**重要**：所有必要的環境變數都必須在 Coolify 界面中設置，應用不再依賴 `.env` 文件。

### 4. 配置持久性卷

在 Coolify 的「卷」部分，添加以下卷映射：

1. 數據卷：
   - 主機路徑：`/data/applications/[app-id]/data`
   - 容器路徑：`/app/data`

2. 日誌卷：
   - 主機路徑：`/data/applications/[app-id]/logs`
   - 容器路徑：`/app/logs`

### 5. 配置端口（可選）

Discord Bot 本身不需要公開端口，但如果您的應用有其他需求，可以在此配置。

### 6. 部署應用

點擊「保存」然後「部署」，Coolify 將自動構建並啟動應用。

## 常見問題排除

### 1. 環境變數問題

如果遇到「.env 是一個目錄」的錯誤，這通常意味著 Coolify 嘗試將環境變數寫入一個已經存在為目錄的路徑。

**解決方案**：
- 確保使用最新版本的 Dockerfile，它不依賴於 `.env` 文件
- 通過 Coolify UI 直接設置所有環境變數
- 檢查是否有腳本嘗試創建或修改 `.env` 文件

### 2. 數據持久化問題

如果在容器重啟後數據丟失：

**解決方案**：
- 確保正確配置了卷映射
- 檢查主機上的目錄權限
- 檢查數據目錄的所有權是否為容器內的 `botuser` (UID 1000)

## 更新應用

更新 Coolify 中的應用很簡單：

1. 將更新推送到 Git 倉庫
2. 在 Coolify 控制台中點擊「重建」或「重新部署」
3. Coolify 將自動拉取最新代碼並重建容器

## 日誌和監控

您可以通過 Coolify 界面查看容器日誌和監控應用狀態：

1. 在應用程序頁面上，點擊「日誌」標籤查看實時日誌
2. 使用「性能」標籤監控資源使用情況

## 進階設置

### 資源限制

在 Coolify 的「高級」設置中，您可以配置：

- CPU 限制
- 內存限制
- 重啟策略

推薦設置：
- 內存限制：至少 512MB
- CPU 限制：至少 0.5 核心
- 重啟策略：always

### 自動更新

您可以配置 Coolify 自動更新應用：

1. 在應用設置中啟用「Webhook」
2. 在 Git 倉庫中設置 webhook，指向 Coolify 提供的 URL
3. 當有新的提交時，Coolify 將自動重建應用 