
## 从零运行

需要 Python 3.10 或更新版本及 Matplotlib：

```bash
python -m venv .venv
# Windows PowerShell：.venv\Scripts\Activate.ps1
# Linux/macOS：source .venv/bin/activate
python -m pip install -r requirements.txt
python run_experiments.py
```

`requirements.lock.txt` 记录原 Python 3.14.4 环境的精确依赖版本，
需要时可用它替代 `requirements.txt`。不要求 WSL 或 LaTeX；
安装依赖后无需联网，也不依赖原项目路径。

统一入口先从零运行基础实验、生成数据，再执行完整重共享、联合前缀检查和绘图。
无需预先提供结果文件。运行失败返回非零退出码；不要使用 `python -O`
或设置 `PYTHONOPTIMIZE`，因为数学检查需要断言。

## 代码

- `legacy/`：有限域基础、前缀秩、重叠曝光、资源模型和 Libra 风格秩实验。


执行后自动生成 `results/`、各基础模块的 `results/` 和 `plots/`、
`legacy/validation/`、`supplement/validation/` 和 `supplement/figures/`。
这些输出目录均已加入 `.gitignore`，不属于源码包；再次运行会覆盖生成结果。
总状态保存在 `results/summary.json`。




来源说明见 `PROVENANCE.md`。实验范围是有限域代数、理想快照和资源模型，
不等于完整恶意移动协议，也不测量真实网络性能。

