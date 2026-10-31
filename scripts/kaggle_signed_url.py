#!/usr/bin/env python
"""Print the signed download URL for one file inside a Kaggle dataset.

The official CLI downloads single-threaded (~130 KB/s here); pairing this URL
with `aria2c -x16` gets 3-6x on the same link.

Usage:
    python tools/kaggle_signed_url.py <owner/dataset> <file_name> [version]
"""
from __future__ import annotations

import sys

from kaggle.api.kaggle_api_extended import ApiDownloadDatasetRequest, KaggleApi


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    dataset = sys.argv[1]
    file_name = sys.argv[2]
    version = int(sys.argv[3]) if len(sys.argv) > 3 else None
    owner_slug, dataset_slug = dataset.split('/', 1)

    api = KaggleApi()
    api.authenticate()
    with api.build_kaggle_client() as client:
        request = ApiDownloadDatasetRequest()
        request.owner_slug = owner_slug
        request.dataset_slug = dataset_slug
        request.dataset_version_number = version
        request.file_name = file_name
        response = client.datasets.dataset_api_client.download_dataset(request)
    print(response.request.url)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
