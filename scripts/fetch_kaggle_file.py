#!/usr/bin/env python
"""Download one Kaggle dataset file with a resumable range downloader."""
from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

import requests
from kaggle.api.kaggle_api_extended import KaggleApi
from kagglesdk.datasets.types.dataset_api_service import (
    ApiDownloadDatasetRequest,
)


ROOT = Path(__file__).resolve().parents[1]
RANGE_DOWNLOADER = ROOT / "scripts" / "parallel_range_download.sh"


def signed_url(dataset: str, file_name: str, version: int | None) -> str:
    owner, slug = dataset.split("/", 1)
    api = KaggleApi()
    api.authenticate()
    with api.build_kaggle_client() as client:
        request = ApiDownloadDatasetRequest()
        request.owner_slug = owner
        request.dataset_slug = slug
        request.dataset_version_number = version
        request.file_name = file_name
        response = client.datasets.dataset_api_client.download_dataset(
            request
        )
    url = getattr(getattr(response, "request", None), "url", None)
    if not url:
        raise RuntimeError("Kaggle returned no signed download URL")
    return url


def content_length(url: str) -> int:
    # A one-byte range also works where a proxy rejects HEAD.
    response = requests.get(
        url,
        headers={"Range": "bytes=0-0", "Accept-Encoding": "identity"},
        timeout=(20, 120),
        stream=True,
    )
    response.raise_for_status()
    response.close()
    value = response.headers.get("Content-Range", "")
    if "/" not in value:
        raise RuntimeError("missing Content-Range; cannot determine file size")
    return int(value.rsplit("/", 1)[1])


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def download(
    url: str,
    output: Path,
    size: int,
    parts: int,
    concurrency: int,
    chunks: Path,
) -> None:
    chunks.mkdir(parents=True, exist_ok=True)
    command = [
        "bash",
        str(RANGE_DOWNLOADER),
        url,
        str(chunks),
        str(size),
        str(parts),
        str(concurrency),
    ]
    subprocess.run(command, check=True)
    part_files = sorted(chunks.glob("part_*.bin"))
    if not part_files:
        raise RuntimeError("range downloader produced no part files")
    assembled = output.with_suffix(output.suffix + ".assembling")
    with assembled.open("wb") as target:
        for part in part_files:
            with part.open("rb") as source:
                shutil.copyfileobj(source, target)
    got = assembled.stat().st_size
    if got != size:
        raise RuntimeError(f"size mismatch: got {got}, expected {size}")
    os.replace(assembled, output)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Download one Kaggle dataset file with range curl."
    )
    parser.add_argument("--dataset", required=True, help="OWNER/DATASET")
    parser.add_argument("--file", required=True, help="file path inside dataset")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--version", type=int, default=None)
    parser.add_argument("--parts", type=int, default=64)
    parser.add_argument("--concurrency", type=int, default=48)
    parser.add_argument(
        "--chunks",
        type=Path,
        default=None,
        help="chunk directory; defaults next to the output file",
    )
    parser.add_argument("--sha256", default=None)
    parser.add_argument(
        "--keep-chunks",
        action="store_true",
        help="retain verified chunk files",
    )
    args = parser.parse_args()
    if args.parts < 1 or args.concurrency < 1:
        raise SystemExit("parts and concurrency must be positive")

    output = args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    chunks = args.chunks or output.parent / (
        "_chunks_" + output.name.replace("/", "_")
    )

    url = signed_url(args.dataset, args.file, args.version)
    size = content_length(url)
    if output.is_file() and output.stat().st_size == size:
        print(f"[skip] {output} already has expected size {size}", flush=True)
    else:
        print(
            f"[fetch] {args.dataset}/{args.file} -> {output} "
            f"({size / 1e6:.1f} MB, parts={args.parts}, "
            f"concurrency={args.concurrency})",
            flush=True,
        )
        download(
            url,
            output,
            size,
            args.parts,
            args.concurrency,
            chunks,
        )

    if output.stat().st_size != size:
        raise SystemExit("final size verification failed")
    if args.sha256:
        got = file_sha256(output)
        if got.lower() != args.sha256.lower():
            raise SystemExit(
                f"SHA256 mismatch: got {got}, expected {args.sha256}"
            )
        print(f"[sha256] {got}", flush=True)
    if not args.keep_chunks:
        shutil.rmtree(chunks, ignore_errors=True)
    print(f"[done] {output} ({size} bytes)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
