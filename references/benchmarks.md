# Benchmarks and Transfer Notes

These are historical measurements from the AutoDL environment used during the
RSNA Knee 2026 project. They are directional; network routing changes over time.

## Kaggle storage

| Method | Approximate throughput |
|---|---:|
| Kaggle CLI single stream | ~0.13–0.2 MB/s in the tested environment |
| `aria2c -x16` direct GCS signed URL | ~1.1 MB/s |
| Parallel byte ranges, 16 curl connections | ~2.5 MB/s |
| Parallel byte ranges, 32 connections | ~4.2 MB/s |
| Parallel byte ranges, 64 connections | ~5.8 MB/s |
| Tuned multi-range corpus transfers | ~4.5–10.4 MB/s |

The 96-slice corpus transfer used `192` ranges and `160` concurrent curls. This
is an aggressive profile; test a small object and watch server-side limits.

## Proxy behavior

- At one point, the AutoDL academic proxy was faster than direct (`2.9` vs
  `1.75 MB/s`).
- Later, the same proxy throttled around 51 connections and fell to
  `0.3–0.9 MB/s`, while direct transfers reached `4.5 MB/s`.
- Resolve Kaggle API/signed URLs without the proxy where it causes TLS or
  latency problems. Apply the proxy to the actual storage transfer only when
  measured.

## HuggingFace and GitHub

- HuggingFace direct access was unreliable in the tested environment.
- `source /etc/network_turbo` plus `HF_ENDPOINT=https://hf-mirror.com`
  succeeded for small model downloads.
- Set `HF_ENDPOINT` before importing `huggingface_hub` or `timm`.
- The proxy is useful for GitHub releases and HuggingFace assets; do not assume
  it improves Kaggle API/upload traffic.

## Defaults

```text
generic large object     parts=64, concurrency=48
aggressive GCS profile   parts=192, concurrency=160
small file fallback      aria2c -x16 -s16 -k1M
curl stall timeout       180 seconds
```

Always measure before choosing a high-concurrency profile.
