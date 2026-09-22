# 开发与维护入口

本仓库同时维护 Python SDK、星核板 V2 与星尘板下位机固件、离线烧录资源和发布脚本。

完整的目录职责、星核板 V2 新功能流程、Arduino Uno 等新板型接入步骤、第三方库规则以及 AI 检查表统一记录在根目录的 [工程维护指南](../MAINTENANCE.md)。后续修改不得另建相互矛盾的目录规则。

常用命令：

```powershell
# Python 测试 + 星核板 V2/星尘板固件编译
.\tools\verify.ps1

# 编译固件、刷新 Python 离线资源并构建 wheel
.\tools\build-wheel.ps1

# 清理 Python 测试和构建缓存（保留 artifacts/dist）
.\tools\clean.ps1
```
