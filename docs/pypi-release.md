# PyPI 发布说明

StarBridge 的 PyPI 发行名是 `starbridge-hardware`，Python 导入名仍然是 `starbridge`。

## 首次发布前的一次性设置

1. 注册并登录 PyPI，验证邮箱并启用双重验证。
2. 在 PyPI 的 Publishing 页面添加 Pending publisher：
   - PyPI project name：`starbridge-hardware`
   - Owner：`HAOTIANGUO22`
   - Repository：`StarBridge`
   - Workflow：`publish-pypi.yml`
   - Environment：`pypi`
3. 在 GitHub 仓库的 Settings → Environments 中创建 `pypi` 环境。建议为该环境启用 required reviewers，防止误发布。

## 发布检查

发布前必须确认：

- `python/pyproject.toml` 与 `python/src/starbridge/_version.py` 的版本一致。
- `python/src/starbridge/_offline/firmware/starcore-v2/manifest.json` 的 `sdk_version` 一致。
- `python/src/starbridge/_offline/firmware/stardust/manifest.json` 的 `sdk_version` 一致，且 `firmware.hex` 哈希匹配。
- `firmware/starcore-v2` 和 `firmware/stardust` 是各自离线固件的唯一源码来源，`_offline` 中的镜像由构建脚本生成。
- wheel 同时包含 esptool 与 avrdude/config/许可证，可分别离线烧录 ESP32 和 AVR。
- 目标版本尚未上传到 PyPI；PyPI 不允许覆盖同名同版本文件。
- `./tools/verify.ps1` 和 `./tools/build-wheel.ps1` 均成功。

## 正式发布

在 GitHub 仓库打开 Actions → Publish Python package to PyPI → Run workflow，可以从主分支手动发布。

也可以从准备发布的主分支提交创建并推送 `pypi-v版本号` 标签，例如：

```powershell
git tag pypi-v4.5.0
git push origin pypi-v4.5.0
```

两种方式都会先运行测试、生成 wheel 并检查元数据，随后通过 PyPI Trusted Publishing 上传，不需要在 GitHub 保存 API Token。
