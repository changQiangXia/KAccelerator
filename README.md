# KAccelerator

一个面向大文件下载的 Codex skill，重点支持 Kaggle dataset、
HuggingFace 模型文件和 GitHub 资源的可恢复、并行传输。

## Skill 入口

```text
SKILL.md
```

脚本在 `scripts/`，传输基准和环境说明在 `references/`。

## 依赖

需要 `bash`、`curl`，以及带 `kaggle`、`kagglesdk`、`requests` 的 Python
环境；`aria2c` 为可选 fallback。

```bash
python -c "import kaggle, kagglesdk, requests; print('ok')"
```

## 快速使用

下载一个 Kaggle dataset 文件：

```bash
python scripts/fetch_kaggle_file.py \
  --dataset OWNER/DATASET \
  --file path/inside/dataset \
  --output downloads/file.bin \
  --parts 64 --concurrency 48
```

已知 URL、大小和 SHA256 时，也可以直接调用通用分块下载器：

```bash
bash scripts/parallel_range_download.sh \
  "$URL" downloads/chunks "$TOTAL_BYTES" 64 48
```

HuggingFace/GitHub：

```bash
source /etc/network_turbo
export HF_ENDPOINT=https://hf-mirror.com
```

## 注意

- 下载源必须支持 HTTP `Range`；服务器返回整文件或 overrun 时脚本会失败退出。
- 大文件下载会保留分块目录，完成尺寸和可选 SHA256 校验后再清理。
- 不要把 Kaggle/HuggingFace token、signed URL 或凭据写进仓库和日志。
- 高并发参数需要结合源站、CPU、内存和磁盘实测调整。
