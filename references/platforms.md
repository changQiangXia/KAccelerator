# Platform Commands

## Kaggle dataset

```bash
python scripts/kaggle_signed_url.py OWNER/DATASET FILE_IN_DATASET
bash scripts/parallel_range_download.sh URL OUT_DIR TOTAL_BYTES 64 48
```

For a dataset archive, prefer downloading named files when the archive endpoint
returns a flaky response.

## HuggingFace

```bash
source /etc/network_turbo
export HF_ENDPOINT=https://hf-mirror.com
python -c "import huggingface_hub; print(huggingface_hub.__version__)"
```

Set the environment before any model library import.

## GitHub

```bash
source /etc/network_turbo
git clone https://github.com/OWNER/REPO.git
```

Use a credential helper or a scoped token for writes. Keep credentials out of
the repository and shell history.

## Long transfer

```bash
setsid nohup bash scripts/parallel_range_download.sh \
  "$URL" "$CHUNK_DIR" "$TOTAL_BYTES" 64 48 \
  >/tmp/download.log 2>&1 < /dev/null &
```

Inspect progress with:

```bash
du -sm "$CHUNK_DIR"
```

Do not poll more frequently than the transfer or platform warrants.
