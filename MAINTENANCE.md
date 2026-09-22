# StarBridge 工程维护指南（人类与 AI 必读）

本文件是仓库目录职责和升级流程的唯一维护入口。任何 AI 或开发者在新增功能、增加板型、升级依赖或发布版本前，都必须先阅读本文件，再阅读与任务直接相关的源码和协议文档。

## 一、不可破坏的目录边界

```text
StarBridge/
├─ firmware/                         下位机固件生产源码
│  ├─ arduino-board-package/         StarBridge 自定义 Arduino 板卡定义
│  ├─ platformio.ini                 PlatformIO 构建入口
│  ├─ shared-libraries/              已被至少两块板验证共用的固定版本库
│  ├─ stardust/                      星尘板（ATmega328P/CH340）固件
│  └─ starcore-v2/                   星核板 V2 的全部固件内容
│     ├─ starcore-v2.ino             Arduino 入口
│     ├─ src/
│     │  ├─ app/                     命令分发与固件应用生命周期
│     │  ├─ board/                   板级外设管理器与引脚约束
│     │  ├─ drivers/                 芯片/总线底层驱动，例如 PN532 I2C
│     │  └─ protocol/                下位机 Protocol V2 编解码与命令号
│     └─ libraries/                  仅星核板 V2 使用的固定版本依赖
├─ python/                           Python SDK 生产源码
│  ├─ src/starbridge/                用户 API、协议客户端、烧录逻辑
│  │  ├─ _offline/                   构建生成并随 wheel 分发的固件/烧录器
│  │  └─ _vendor/                    为离线安装固定存放的 Python 依赖
│  └─ tests/                         Python SDK 与协议自动测试
├─ docs/                             协议、引脚、发布、示例与测试文档
├─ tools/                            获取工具链、验证、构建和清理脚本
├─ artifacts/                        可删除、可重建的构建结果和测试产物
├─ .github/workflows/                GitHub 自动测试和发布流程
├─ README.md                         用户入口
├─ THIRD_PARTY_NOTICES.md            第三方依赖版本、来源和许可证
└─ MAINTENANCE.md                    本维护规则
```

强制规则：

1. `python/` 只维护电脑端 API、通信、烧录和 Python 测试，不放 C/C++ 固件源码。
2. 某块板的固件、板级驱动和专用库必须放进 `firmware/<board>/`。星核板 V2 的新代码只能进入 `firmware/starcore-v2/`。
3. `artifacts/` 只放生成物，不能作为源码目录、Git worktree 或第三方库的长期存放位置。
4. `python/src/starbridge/_offline/` 是构建脚本生成的发布副本。不要手工修改其中的 `.bin` 或哈希；修改固件源码后运行 `tools/build-wheel.ps1` 更新。
5. 不要在仓库根目录随意下载第三方项目。板专用依赖放进该板的 `libraries/`，并只保留编译必需源码、元数据和许可证。
6. 不要为“以后可能复用”提前创建共享库目录。只有同一份库已经被至少两个板型使用时，才允许提取到 `firmware/shared-libraries/`，并同步修改所有构建入口。
7. 临时隔离开发需要 Git worktree 时，放在仓库外的临时目录或同级目录，绝不能放进 `artifacts/`。

## 二、根目录和生成目录说明

- `.git/`：Git 历史、分支和 worktree 元数据，不手工编辑。
- `.github/`：持续集成与 PyPI 发布配置。
- `.venv/`：本机 Python 虚拟环境，可删除重建，不提交。
- `.pytest_cache/`、`__pycache__/`：测试和解释器缓存，可随时删除。
- `artifacts/dist/`：wheel、Mind+ 扩展等发布候选产物。确认已上传或可重建后可以删除。
- `tools/arduino-cli/`：脚本下载的 Arduino CLI 缓存，可删除；`bootstrap-arduino.ps1` 会重建。
- `%LOCALAPPDATA%/StarBridge/`：为避开中文路径导致的 ESP32 链接问题而使用的固件中间构建目录，可删除。

## 三、给星核板 V2 增加功能

以增加一个新 I2C/SPI/UART 外设为例，按以下顺序修改，不能只改 Python 或只改固件：

1. 在 `docs/protocol-v2.md` 设计请求和响应格式，确认命令号没有被占用。
2. 在 `firmware/starcore-v2/src/protocol/Protocol.h` 增加全局唯一命令号。
3. 在 `firmware/starcore-v2/src/drivers/` 实现芯片或总线协议。驱动不应知道 StarBridge 串口协议。
4. 在 `firmware/starcore-v2/src/board/` 增加板级管理器，负责引脚合法性、状态和资源生命周期。
5. 在 `firmware/starcore-v2/src/app/CommandDispatcher.*` 接入命令，严格检查长度和参数，并更新能力位。
6. 在 `python/src/starbridge/constants.py` 添加相同命令号，在独立模块中实现用户 API，再由 `board.py` 暴露工厂方法，并从 `__init__.py` 导出公共类型。
7. 在 `python/tests/` 添加成功、边界、错误状态和编码测试；在 `docs/examples.html` 增加用例。
8. 若最低兼容固件发生变化，更新 `python/src/starbridge/boards.py`；同时更新固件版本、SDK 版本和离线 manifest。
9. 运行 `tools/verify.ps1`，再做真实硬件测试。没有接入实物的功能必须明确标注“编译通过、实机待测”。
10. 发布时运行 `tools/build-wheel.ps1`；脚本会从源码编译固件、刷新 `_offline`、生成 manifest 哈希并构建 wheel。

PN532 是上述结构的示例：

- Python API：`python/src/starbridge/pn532.py`
- 板级管理器：`firmware/starcore-v2/src/board/Pn532Manager.*`
- 精简 I2C 驱动：`firmware/starcore-v2/src/drivers/Pn532I2c.*`
- 不依赖 DFRobot PN532，也不维护完整 Adafruit PN532/BusIO 仓库。

网络功能遵循同一边界：ESP32 原生 Wi-Fi、ESP-NOW、SNTP 和硬件附近的软串口代码放在 `firmware/starcore-v2/src/board/`；需要密钥、HTTPS 和大响应体的天气、语音识别、大模型及时区 API 放在 `python/src/starbridge/cloud.py`。密钥只能从环境变量或运行时参数传入，不能写入固件、示例或仓库。

## 四、创建新板型（以 Arduino Uno 为例）

新板型不能直接把代码塞进 `starcore-v2`，应创建平行目标：

```text
firmware/
├─ starcore-v2/
└─ arduino-uno/
   ├─ arduino-uno.ino
   ├─ src/
   │  ├─ app/
   │  ├─ board/
   │  ├─ drivers/
   │  └─ protocol/
   └─ libraries/
```

具体步骤：

1. 先确定板型标识：目录名、Python `BoardType`、协议 `board_id`、离线固件目录名必须稳定且一一对应。
2. 创建 `firmware/arduino-uno/`，实现 Uno 自己的引脚表、能力位、命令分发和 Protocol V2 串口入口。
3. 优先使用官方 FQBN `arduino:avr:uno`。只有自定义硬件参数或变体时，才在 `firmware/arduino-board-package/hardware/starbridge/avr/` 新建 `boards.txt`、`platform.txt` 和 variant。
4. Uno 专用库放 `firmware/arduino-uno/libraries/`。若某依赖后来同时被 Uno 和星核板使用，再经过兼容性验证后提取为共享库。
5. 在 `python/src/starbridge/boards.py` 增加板型配置，包括板 ID、USB 识别、最低固件版本、烧录方式和支持能力。
6. 在 `python/src/starbridge/programmer.py` 增加 AVR/avrdude 烧录后端，不能把 ESP32 的 esptool 参数硬套给 Uno。
7. 在 `python/src/starbridge/_offline/firmware/arduino-uno/` 生成 Uno 固件及独立 manifest；在 `_offline` 中加入所需烧录器和许可证。
8. 扩展 `tools/verify.ps1`，分别编译每个受支持板型；扩展 `tools/build-wheel.ps1`，为每块板生成并校验离线资源。
9. 为“板型选择、错误板型拒绝、能力差异、烧录命令”增加自动测试，并新增引脚文档。
10. 至少用一块真实 Uno 完成连接、烧录、重启、Ping、GPIO 和一项外设回归后，才能标为正式支持。

Protocol V2 的命令号是跨板型全局命名空间。板型不支持某个命令时应返回 `UNSUPPORTED`，不能在不同板上把同一命令号解释成不同功能。

## 五、第三方库规则

引入或升级库时必须同时完成：

1. 确认许可证允许当前分发方式。
2. 固定版本号或提交哈希，禁止依赖构建时自动拉取“最新版”。
3. 只保留生产编译所需文件和许可证；删除上游示例、截图、CI 配置及与目标 MCU 无关的源码。
4. 在 `THIRD_PARTY_NOTICES.md` 记录路径、来源、版本/提交和许可证。
5. 完整编译所有受影响板型，并检查最终 wheel 不意外包含 C/C++ 源码。

优先写小型、可审查的板内驱动；只有成熟通用库明显降低风险时才整体引入第三方依赖。

## 六、版本与发布规则

- Python SDK 版本同时更新 `python/pyproject.toml` 和 `python/src/starbridge/_version.py`。
- 固件版本来自 `GET_INFO`，并同步写入离线 manifest。
- Protocol V2 仅在帧格式不兼容时提升主协议版本；新增兼容命令不应随意改变协议主版本。
- 新功能需要提高最低固件要求时，同步更新 `python/src/starbridge/boards.py`。
- 发布前依次运行：

```powershell
.\tools\verify.ps1
.\tools\build-wheel.ps1
```

- `verify.ps1` 必须通过 Python 测试和所有正式板型的固件编译。
- `build-wheel.ps1` 是生成 `_offline` 固件、manifest 和 wheel 的唯一入口。
- PyPI 发布细节见 `docs/pypi-release.md`。

## 七、AI 完成任务前检查表

- 是否把源码放进了正确板型目录，而不是 `artifacts/`？
- 是否同时修改了协议、固件、Python API、测试和文档？
- 是否避免引入完整且未裁剪的第三方仓库？
- 是否保留第三方许可证并更新声明？
- 是否更新能力位、版本和最低兼容固件？
- 是否运行 Python 测试和固件编译？
- 是否清楚区分“自动测试通过”“固件编译通过”和“实机验证通过”？
- 是否只清理生成物，没有删除用户源码或历史发布包？

不满足以上任一项时，不应声称任务已经完成。
