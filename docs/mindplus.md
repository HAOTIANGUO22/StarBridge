# Mind+ 安装与使用

StarBridge 4.5.1 增加 Python 3.8 兼容支持，适用于 Mind+ 自带的 Windows 64 位 Python 3.8.5。安装名仍然是 `starbridge-hardware`，代码仍然使用 `from starbridge import ...`，无需额外安装一个同名功能的库。

本次更新仅修改电脑端 SDK，沿用 4.5.0 的 StarCore V2 / StarDust 固件镜像与烧录器。现有兼容固件可以继续使用。

## 安装本地 wheel

将 `starbridge_hardware-4.5.1-py3-none-any.whl` 保存到电脑。

在 PowerShell 中使用 **Mind+ 自己的解释器** 安装。下面会使用当前 Windows 账号，不必手动替换用户名；若 Mind+ 安装在其他位置，请修改第一行：

```powershell
$mindplusPython = "$env:USERPROFILE\Documents\mindplus-py\environment\Python3.8.5-64\python.exe"
& $mindplusPython -m pip install --no-deps "D:\下载\starbridge_hardware-4.5.1-py3-none-any.whl"
& $mindplusPython -c "import sys, starbridge; print(sys.version); print(starbridge.__version__); print(starbridge.__file__)"
```

请将 wheel 路径替换为实际保存位置。本地安装不经过镜像源，不需要升级 pip。支持 Mind+ 原有的 pip 22.0.4。

## 从 PyPI 或镜像安装

只有在 4.5.1 正式发布并同步后，才可在 Mind+ 的 Python 库管理中安装 `starbridge-hardware==4.5.1`，或执行：

```powershell
& $mindplusPython -m pip install "starbridge-hardware==4.5.1" -i https://pypi.tuna.tsinghua.edu.cn/simple/
```

4.5.0 及更早版本不支持 Python 3.8。`No matching distribution found` 可能来自版本不兼容，不能仅凭该提示判断镜像缺包。

## 在 Mind+ Python 模式中验证

安装后重新运行程序；若之前已有程序进程加载旧版库，先停止程序或重启 Mind+。

```python
import sys
import starbridge
from starbridge import Board, BoardType

print(sys.version)
print(starbridge.__version__)  # 4.5.1

with Board.begin(BoardType.STARCORE_V2) as board:
    print(board.info())
```

星尘板使用 `BoardType.STARDUST`。连接多个板卡时，可加上实际串口，例如 `Board.begin(BoardType.STARCORE_V2, port="COM7")`。

`Board.begin()` 会在需要时自动烧录固件。wheel 已包含离线镜像与 Windows x86-64 烧录器，不需要另外安装 Arduino IDE、Arduino CLI、pyserial 或 typing_extensions。

安装到电脑上的另一个 Python 环境不会使 Mind+ 自动获得这个库。请以 `sys.executable`、`starbridge.__file__` 的实际输出确认环境。
