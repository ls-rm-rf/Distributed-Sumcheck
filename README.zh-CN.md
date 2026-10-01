# 论文实验

English instructions: [README.md](README.md).

## 从零运行

需要 Python 3.10 或更新版本。在本目录执行：

```bash
python -m venv .venv
# Windows PowerShell：.venv\Scripts\Activate.ps1
# Linux/macOS：source .venv/bin/activate
python -m pip install -r requirements.txt
python run_experiments.py
```

`requirements.lock.txt` 记录原 Python 3.14.4 环境的依赖版本，
需要使用这些版本时，可用它替代 `requirements.txt`。
不要求 WSL 或 LaTeX；安装依赖后，运行无需联网，也不依赖实验包外的文件。

统一入口依次运行基础实验、完整刷新检查、公开记录与快照的联合检查、
完整刷新成本比较和恢复时期数绘图。读取结果前会先生成所需基础数据。
失败时返回非零退出码。不要使用 `python -O` 或设置 `PYTHONOPTIMIZE`，
因为数学检查使用断言。

## 代码结构

| 路径 | 内容 |
|---|---|
| `legacy/crypto_core/` | 有限域、多项式、秩和 Shamir 共享工具 |
| `legacy/exp1_rank_saturation/` | 稀疏掩码的前缀秩实验 |
| `legacy/exp2_barrier/` | 重叠曝光、跨时期恢复、完整刷新和快照隐私实验 |
| `legacy/exp3_communication/` | 资源模型、参数扫描和完整刷新成本比较 |
| `legacy/appendix_a_libra_rank/` | 统一次数的分离掩码秩实验 |

完整刷新及快照检查已经并入对应实验模块：

| 脚本 | 验证内容 |
|---|---|
| `legacy/exp2_barrier/verify_complete_refresh.py` | 采样器的精确分布、跨时期攻击、条件独立性、自适应快照和提升空间秩 |
| `legacy/exp2_barrier/check_prefix_snapshots.py` | 公开记录与快照的联合分布及相关反例 |
| `legacy/exp2_barrier/make_fig_epochs.py` | kernel-only 更新下的恢复时期数曲线 |
| `legacy/exp3_communication/check_complete_refresh_costs.py` | 98 组完整刷新预算、与 392 条基础总成本的比较及模型图 |

完成一次完整运行后，也可从实验包根目录用 `python <脚本路径>` 单独执行。
采样器和成本脚本需要完整基础数据；缩小规模的扫描不能用于成本比较。

## 输出文件

| 路径 | 输出 |
|---|---|
| `results/` | 各阶段日志及总状态 `summary.json` |
| `legacy/validation/` | 基础实验日志和哈希清单 |
| 各基础模块的 `results/`、`plots/` | 基础 CSV/JSON 数据和图片 |
| `legacy/exp2_barrier/validation/` | `paper_checks.json`、`prefix_checks.json` 和 `lifted_rank.csv` |
| `legacy/exp2_barrier/figures/` | `epochs_to_recovery.pdf` 和 PNG 预览 |
| `legacy/exp3_communication/validation/` | `completed_costs.csv` 和 `completed_cost_checks.json` |
| `legacy/exp3_communication/figures/` | `refresh_dimensions`、`completed_cost` 的 PDF/PNG 图片 |

输出目录和本地虚拟环境已加入 `.gitignore`。
源码发布包含脚本、依赖说明和文档；输出由统一入口重新生成，
后续运行会覆盖这些生成文件。

## 实验范围

实验验证有限域代数、理想被动快照和声明的资源模型，
不实现完整恶意移动分布式服务，也不测量真实网络性能。
代码来源见 `PROVENANCE.md`。
