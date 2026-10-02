# Headroom 仪表盘中文语言包

为 [Headroom](https://pypi.org/project/headroom-ai/)（`headroom-ai`）代理的实时仪表盘提供简体中文界面的**单文件语言包**。

- **不改动 Headroom 本体**：不修改其任何文件
- **不依赖开机自启**：仅借助 Python 官方机制惰性生效
- **卸载零残留**：删掉一个文件即恢复英文

---

## 安装（三步）

### 1. 找到你的 Python user-site 目录

这一步只是确定文件该放哪里，与 PATH 无关：

```bash
python -m site
# 看 USER_SITE 那一行，例如：
# C:\Users\<你>\AppData\Roaming\Python\Python313\site-packages
```

### 2. 放入语言包

把本仓库的 [`usercustomize.py`](usercustomize.py) 放进该目录（目录不存在就手动创建）。

也可以用一条命令直接下载安装：

```bash
python -c "import site, pathlib, urllib.request; p = pathlib.Path(site.USER_SITE); p.mkdir(parents=True, exist_ok=True); urllib.request.urlretrieve('https://raw.githubusercontent.com/2972218256/headroom-dashboard-zh/main/usercustomize.py', p / 'usercustomize.py'); print('已安装到', p)"
```

### 3. 重启并访问

重启 Headroom 代理（无论它是前台 `headroom proxy`、pythonw 后台还是任务计划启动），打开
<http://127.0.0.1:8787/dashboard> 即为中文。

---

## 工作原理

CPython 每次启动都会自动导入 user-site 目录下的 `usercustomize.py`（官方机制）。本文件在此基础上注册一个惰性导入钩子：

- **平时什么都不做**——只有当某个 Python 进程导入 `headroom.dashboard`（即代理进程）时才激活；
- 激活后把仪表盘和设置页的读取函数包装为「读取官方英文模板 → 套用内置映射表 → 返回中文」，结果按模板文件的 `(mtime, size)` 缓存；
- **不改写 Headroom 的任何文件**；翻译过程中任何异常都会回退为英文原版，绝不影响代理运行。

---

## 升级 Headroom 后

**无需任何操作。** `pip upgrade headroom-ai` 会把模板覆盖回英文，但语言包按模板哈希缓存——刷新页面即自动按新版英文重新翻译。

- 新版本**新增**的界面文案会保持英文原样显示（不会硬套旧翻译，不会导致功能异常）；
- 欢迎提 PR 把新词条补进映射表（映射表就在 `usercustomize.py` 顶部，纯「英文 → 中文」键值对）。

---

## 已验证兼容性

| headroom-ai | 状态 |
|---|---|
| 0.39.1 | ✅ 完整汉化（Windows 11 / Python 3.13 实测） |

其他版本可用，未覆盖的新词条保持英文。

---

## 刻意保留英文的内容

以下内容是后端数据值或技术标识，翻译会破坏功能或语义，因此保留：

- 客户端名（`coding`、`claude`、`openai` 等）与后端状态枚举（如输出整形卡片的 `INACTIVE`）
- 流水线阶段名（`_deep_copy`、`content_router` 等）与浪费类型键名（`json_bloat` 等）
- 单位与环境变量（`tok/s`、`ms`、`TTL 1h`、`HEADROOM_OUTPUT_SHAPER=1`）

---

## 卸载

删除 user-site 目录下的 `usercustomize.py`，重启代理即恢复英文。

---

## 网络受限环境

如果你的 hosts 或网络屏蔽了 GitHub 导致下载失败，可从本仓库页面直接复制 `usercustomize.py` 的内容另存为文件（UTF-8 编码），放入 user-site 目录即可——语言包本身不依赖任何网络。

---

## License

[MIT](LICENSE)
