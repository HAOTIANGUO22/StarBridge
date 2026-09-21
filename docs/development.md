# 公开 SDK 开发指南

本仓库负责 StarBridge 的公开 Python API、通信协议、用户文档、示例和经过校验的预编译固件制品。

## 可公开修改的范围

- `python/src/starbridge/`：Python SDK、串口通信和用户级外设 API。
- `python/tests/`：公开 SDK 与协议测试。
- `docs/`：协议、引脚、示例和排障文档。
- `tools/`：公开 wheel 的验证和打包脚本。

## 固件边界

下位机 C/C++ 生产源码、板卡定义、Arduino 依赖和固件构建流程在私有仓库维护。私有流程输出 `_offline` 目录，公开流程只校验并打包以下制品：

```text
firmware/starcore-v2/*.bin
firmware/starcore-v2/manifest.json
windows-x86_64/esptool.exe
windows-x86_64/ESPTOOL_LICENSE.txt
```

公开仓库不接受下位机源文件、构建缓存或签名密钥。

## 验证

```powershell
.\tools\verify.ps1
.\tools\build-wheel.ps1
```

发布前必须确认 wheel 不包含 `.c`、`.cpp`、`.h`、`.ino`、Arduino 板卡包或私有构建脚本。
