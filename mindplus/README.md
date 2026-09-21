# StarBridge for Mind+ V1

这是 StarBridge 4.3 的 Mind+ V1 Python 模式用户库，要求 Mind+ 1.7.1 或更高版本。

当前扩展版本：`0.2.1`。

## 当前范围

- 自动识别串口、指定串口连接和强制重新烧录
- GPIO 模式、数字输入输出
- ADC 原始值和毫伏读取、DAC 输出
- PWM 配置、写入和停止
- DHT11 温湿度、超声波距离
- 外设状态复位和关闭连接

OLED、WS2812 和 MP3 积木将在后续迭代加入。

DHT11 温度和湿度积木共享 1 秒读数缓存；传感器偶发无响应时会自动等待并重试，避免连续读取触发状态 5。

## 开发版加载

1. 打开 Mind+ V1.7.1 或更高版本并进入 Python 模式。
2. 在扩展中选择“用户库”，加载本目录的 `config.json`。
3. 把“连接星核板 V2”积木放在其他 StarBridge 积木之前。

Mind+ V1 使用较旧的 Python 运行环境，不能直接安装要求 Python 3.10+ 的 StarBridge 4.3 wheel。本扩展因此自带 `starbridge_mindplus.py` 兼容层、StarCore V2 固件和 Windows 离线烧录器。连接积木会自动发现 CP210x/CH9102 串口；没有兼容固件时会自动烧录，然后通过 Protocol V2 连接。

## 导出

运行仓库根目录下的 `tools/build-mindplus-v1.ps1`，输出位于 `artifacts/dist`。`.mpext` 是可直接导入 Mind+ 的 ZIP 格式用户库。
