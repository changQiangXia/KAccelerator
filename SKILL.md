---
name: kaggle-download-accelerator
description: Use for resumable, parallel downloads of Kaggle competition or dataset assets, HuggingFace model files, and GitHub releases when single-connection transfers are slow or unstable.
---

# Kaggle Download Accelerator

Use this skill for large or flaky transfers. The desired outcome is a verified,
resumable download with bounded concurrency and clear provenance.

## Runtime

Use a Python environment with `kaggle`, `kagglesdk`, and `requests`, plus
`curl`; `aria2c` is optional for the fallback path. Verify the environment
before the first transfer:

```bash
python -c "import kaggle, kagglesdk, requests; print('download dependencies ok')"
```

## Route the transfer

1. **Kaggle dataset file:** resolve a signed URL with
   `scripts/kaggle_signed_url.py`, then use
   `scripts/parallel_range_download.sh` or `scripts/fetch_kaggle_file.py`.
2. **Large generic HTTP/GCS object:** use `parallel_range_download.sh` with the
   known size. Start with `parts=64`, `concurrency=48`; a short A/B test can
   justify `192/160` for the measured AutoDL/GCS path.
3. **Kaggle kernel output:** use an explicit-version helper; aria2 is a useful
   fallback for small/medium files.
4. **HuggingFace:** set `HF_ENDPOINT` before importing `huggingface_hub`,
   `timm`, or model libraries.
5. **GitHub:** source the AutoDL academic proxy for normal Git/HTTP access.

Read [references/platforms.md](references/platforms.md) for commands and
[references/benchmarks.md](references/benchmarks.md) before choosing
concurrency or assuming the proxy is faster.

## Operating rules

- Determine object size before splitting it. Validate each range and the final
  assembled file.
- Keep chunk directories until the assembled file has the expected size and
  checksum. Move or delete chunks only after verification.
- The source must honor HTTP `Range`. An overrun or `200` response means the
  server ignored the range; stop and use another endpoint or a single-stream
  downloader.
- Use a stall timeout. A hung range must not block the whole transfer.
- Check source-server limits, container CPU/memory, and disk capacity before
  raising concurrency.
- Keep signed URLs, Kaggle tokens, cookies, and HuggingFace tokens out of Git,
  notebooks, process arguments, and logs.
- Start long transfers with `setsid nohup` and monitor at bounded intervals.
- For ZIPs run `unzip -t`; for NumPy/PyTorch artifacts load or hash them before
  declaring success.

## Scripts

### `scripts/parallel_range_download.sh`

```bash
bash scripts/parallel_range_download.sh URL OUT_DIR TOTAL_BYTES [PARTS] [CONCURRENCY]
```

It writes `part_*.bin` and `todo.txt`; re-running resumes existing chunks.

### `scripts/kaggle_signed_url.py`

```bash
python scripts/kaggle_signed_url.py OWNER/DATASET FILE [VERSION]
```

Use the Kaggle API configuration already present in the environment. Never
print a token.

### `scripts/fetch_kaggle_file.py`

```bash
python scripts/fetch_kaggle_file.py \
  --dataset OWNER/DATASET \
  --file PATH/IN/DATASET \
  --output DOWNLOADS/FILE \
  --parts 64 --concurrency 48
```

Add `--sha256 EXPECTED_SHA256` when the publisher provides a hash.

### `scripts/download_watch.sh`

```bash
setsid nohup bash scripts/download_watch.sh CHUNK_DIR TOTAL_MB 900 \
  >/tmp/download-watch.log 2>&1 &
```

This is a monitor, not an accelerator.

## Failure handling

- **404 from Kaggle CLI:** try the individual file path instead of the archive
  endpoint, then resolve a signed URL.
- **IncompleteRead / truncated response:** retry that range only; preserve
  good chunks.
- **Connection stalls:** reduce concurrency or shorten `CURL_MAX_TIME`; avoid
  restarting the whole object.
- **Proxy slows down:** retry the same signed object directly. The best route
  can change by time and host.
- **Checksum mismatch:** discard only the final assembled file, inspect chunk
  sizes and response headers, and retry the affected range.
