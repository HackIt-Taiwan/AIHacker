# Bug修復記錄

## IGNORED_CHANNELS未定義修復 (2024-03-27)

### 問題描述
機器人啟動後在處理消息時出現錯誤：`NameError: name 'IGNORED_CHANNELS' is not defined`，導致無法正常處理消息。

### 修復方案
在main.py中添加了空的`IGNORED_CHANNELS`列表定義：
```python
# 設置空的IGNORED_CHANNELS列表，表示不屏蔽任何頻道
IGNORED_CHANNELS = []
```

### 影響範圍
- 修復前：機器人無法正常處理任何消息，會在每條消息處理時報錯
- 修復後：機器人能夠正常處理所有頻道的消息，不會忽略任何頻道

### 相關配置
如果未來需要屏蔽特定頻道，可以在`IGNORED_CHANNELS`列表中添加頻道ID，例如：
```python
# 屏蔽特定頻道，這些頻道中的消息將不會被處理
IGNORED_CHANNELS = [11111111111111, 22222222222222]
``` 