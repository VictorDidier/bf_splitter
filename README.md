# bf_splitter

`bf_splitter` is a Python CLI for splitting multi-series microscopy images (for example multi-position or multi-timepoint Bio-Formats files) into individual single-series OME-TIFF files. It separates bright-field and fluorescence channels into different output folders and preserves OME metadata for each extracted series.

## Why this project exists

Modern microscopy acquisitions often store multiple image series in a single file. This tool helps convert those large multi-series files into manageable single-series outputs that are easier to inspect, process, and archive.

Typical use cases include:

- splitting a multi-position `.nd2` file into one TIFF per series
- storing bright-field and fluorescence channels in separate output directories
- writing OME-compatible TIFF files with embedded metadata

## Features

- reads multi-series Bio-Formats inputs through `bffile`
- extracts bright-field and fluorescence channels separately
- writes TIFF outputs as OME-style compatible files
- supports sequential or batched parallel extraction
- supports either threaded or process-based parallelism
- optionally applies TIFF compression (`lzw` or `jpeg2000`)

## Repository layout

- `src/bf_splitter/series_splitter.py` — CLI entry point and extraction workflow
- `src/bf_splitter/metadata_handler.py` — OME metadata extraction and remapping
- `src/bf_splitter/image_writer.py` — TIFF writing logic
- `src/bf_splitter/utils.py` — helper functions for metadata handling and timing
- `src/bf_splitter/verifier.py` — verification utilities (work in progress)
- `pyproject.toml` — package metadata and CLI entry point
- `environment.yml` / `Dockerfile` — environment setup options

## Requirements

- Python 3.12+
- `tifffile`
- `bffile`
- `loguru`
- `imagecodecs`

## Installation

### Local environment with pip

```bash
python -m pip install -e .
```

### Conda environment

```bash
conda env create -f environment.yml
conda activate bf_splitter-env
```

### Docker

```bash
docker build -t bf_splitter .
```

## Usage

After installation, the CLI is available as:

```bash
split-series --input_image /path/to/input.nd2 --outdir /path/to/output_dir
```

### Common options

```bash
split-series \
  --input_image /path/to/input.nd2 \
  --outdir /path/to/output_dir \
  --compression_algorithm lzw \
  --batch_size 4 \
  --concurrency_model threads
```

Available arguments:

- `-i, --input_image` — path to the input multi-series image
- `-o, --outdir` — output directory root
- `-comp, --compression_algorithm` — `lzw` or `jpeg2000`
- `-batch, --batch_size` — number of series to process in parallel
- `-con, --concurrency_model` — `threads` or `processes`
- `-v, --version` — print the package version

## Output structure

The tool creates a directory tree like this:

```text
output/
├── BrightField/
│   ├── sample_xy00.ome.tif
│   ├── sample_xy01.ome.tif
│   └── ...
└── Fluorescence/
    ├── sample_xy00.ome.tif
    ├── sample_xy01.ome.tif
    └── ...
```

- `BrightField/` contains bright-field series
- `Fluorescence/` contains non-bright-field channels
- each TIFF includes OME metadata appended to the TIFF comment block

## Example

```bash
split-series \
  --input_image /data/multipoint.nd2 \
  --outdir /data/processed \
  --compression_algorithm lzw \
  --batch_size 2 \
  --concurrency_model processes
```

This writes extracted TIFFs to:

```text
/data/processed/BrightField/
/data/processed/Fluorescence/
```

## Notes

- This project is designed around microscopy image splitting workflows and is particularly useful for large multi-series acquisitions.
- Parallel processing can substantially improve throughput, but memory usage depends on image size and batch size.
- The project is under active development and some verification tooling is still in progress.

## License

This project is distributed under the BSD-3-Clause license as declared in `pyproject.toml`.
