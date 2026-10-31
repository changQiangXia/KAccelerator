#!/usr/bin/env python
"""Download selected output files from an explicit Kaggle kernel version."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from kaggle.api.kaggle_api_extended import KaggleApi
from kagglesdk.kernels.types.kernels_api_service import (
    ApiDownloadKernelOutputRequest,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--kernel",
        required=True,
        help="owner/kernel-slug",
    )
    parser.add_argument("--version", type=int, required=True)
    parser.add_argument("--file", action="append", required=True)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()

    api = KaggleApi()
    api.authenticate()
    owner, slug, _ = api.parse_kernel_string(args.kernel)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    with api.build_kaggle_client() as client:
        for name in args.file:
            request = ApiDownloadKernelOutputRequest()
            request.owner_slug = owner
            request.kernel_slug = slug
            request.file_path = name
            request.version_number = args.version
            response = client.kernels.kernels_api_client.download_kernel_output(
                request
            )
            response.raise_for_status()
            target = out_dir / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(response.content)
            rows.append(
                {
                    "file": name,
                    "bytes": len(response.content),
                    "status": response.status_code,
                }
            )
    print(
        json.dumps(
            {
                "kernel": args.kernel,
                "version": args.version,
                "out_dir": str(out_dir),
                "files": rows,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
