# Docker 支援更新 (2024-03-31)

## 更新內容

本次更新為 AIHacker Discord Bot 新增了 Docker 支援，允許使用者透過容器化技術輕鬆部署和運行機器人服務，並特別優化了雲端環境和 Coolify 平台部署。

### 新增功能

- **Dockerfile**: 為應用程式建立了專用的 Docker 容器化配置
- **docker-compose.yml**: 提供了簡便的容器協調配置
- **資料持久化**: 通過卷掛載確保資料庫和日誌資料的持久保存
- **環境變數優先**: 優化為優先使用環境變數，不再依賴 `.env` 檔案
- **非 root 用戶運行**: 增強安全性，容器內使用非特權用戶運行應用
- **雲端友好設計**: 針對雲端環境優化，支援雲端平台的密鑰管理系統
- **Coolify 平台支援**: 特別優化以解決 Coolify 部署環境中的常見問題
- **時區設定**: 預設配置為台灣時區 (Asia/Taipei)
- **自動重啟**: 配置容器在發生錯誤時自動重啟

### 技術實現

1. **容器基礎鏡像**:
   - 使用 `python:3.10-slim` 作為基礎鏡像，平衡了鏡像大小和功能性

2. **環境變數優化**:
   - 修改 `config.py` 以優先使用環境變數（`load_dotenv(override=False)`）
   - 提供透明的啟動腳本，顯示環境變數加載狀態
   - 完全移除對 `.env` 檔案的依賴，解決 Coolify 平台的目錄衝突問題

3. **安全性增強**:
   - 創建並使用非 root 用戶 `botuser` 運行應用
   - 合理設置資料夾權限
   - 提供適合雲端環境的配置選項，避免將敏感資訊直接掛載到容器中

4. **資料持久化**:
   - 為 `data/` 目錄配置卷掛載，確保資料庫檔案持久保存
   - 為 `logs/` 目錄配置卷掛載，保存應用日誌
   - 使用環境變數或 `env_file` 進行配置管理，更適合雲端環境

5. **多平台支援**:
   - 本地開發: 支援 docker-compose 與 .env 文件組合
   - 雲端部署: 支援直接注入環境變數
   - Coolify 特定優化: 解決特定平台的目錄結構衝突問題

6. **容器健康檢查**:
   - 實現基本的容器健康檢查機制，確保服務可用性

## 部署說明

詳細的部署指南請參考:
- [Docker 部署指南](../docker_deployment.md) - 適用於一般環境
- [Coolify 部署指南](../coolify_deployment.md) - 專為 Coolify 平台優化

### 本地開發使用方法

1. 準備環境檔案:
   ```bash
   cp .env.example .env
   # 編輯 .env 檔案填寫必要的設定
   ```

2. 啟動服務:
   ```bash
   docker-compose up -d
   ```

### Coolify 環境使用方法

1. 不使用 docker-compose.yml，直接使用 Dockerfile 
2. 通過 Coolify 界面設置所有環境變數
3. 確保正確配置卷映射:
   - `/data/applications/[app-id]/data:/app/data`
   - `/data/applications/[app-id]/logs:/app/logs`

## 效能提升

- **輕量級容器**: 使用精簡的基礎鏡像減少資源消耗
- **快速啟動**: 透過合理的依賴管理加速容器啟動過程
- **自動化部署**: 簡化了跨平台部署流程
- **雲端適配**: 配置優化適合各種雲端平台，包括 AWS, Azure, GCP 和 Coolify

## 注意事項

- Docker 部署需要主機安裝 Docker 和 Docker Compose（本地開發）
- 初次使用 Docker 的用戶建議先閱讀 [Docker 官方文檔](https://docs.docker.com/)
- 雲端環境建議使用環境變數或密鑰管理系統，不要依賴 `.env` 檔案
- Coolify 用戶請特別參考 [Coolify 部署指南](../coolify_deployment.md) 避免環境變數問題 