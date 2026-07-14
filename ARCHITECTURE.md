# GeoCOCO Pipeline Architecture

## 1) Purpose

Pipeline for converting geospatial source data:
- rasters in GeoTIFF,
- labels in SHP/GPKG,

into:
- COCO instance-segmentation dataset (pixel coordinates),
- external geospatial index files for deterministic inverse mapping of model predictions back to source CRS coordinates.

---

## 2) High-level flow

`Ingest -> Normalize CRS -> Tile rasters -> Clip vectors per tile -> Project to pixel coords -> Export COCO -> Export Geo Index -> QA`

Two parallel outputs:
1. `processed/coco/*.json` - model-ready dataset
2. `processed/geo_index/*` - lineage and coordinate recovery metadata

---

## 3) Suggested repository structure

```text
repo/
  pyproject.toml
  README.md
  configs/
    dataset.yaml
  src/
    geococo/
      __init__.py
      config.py
      io/
        raster.py
        vector.py
      crs/
        normalize.py
      tiling/
        generate_tiles.py
      annotations/
        clip_project.py
        coco_builder.py
      geo_index/
        tile_index.py
        annotation_index.py
      inverse/
        restore_geoms.py
      qa/
        validators.py
        stats.py
      cli.py
  notebooks/
    00_exploration.ipynb
    01_pipeline_debug.ipynb
  tests/
    test_crs.py
    test_tiling.py
    test_coco_export.py
    test_inverse_restore.py
  data/
    raw/
    interim/
    processed/
      coco/
      geo_index/
```

---

## 4) Data contracts (schemas)

Recommended format for index tables: `Parquet`.

### 4.1 `tile_index.parquet`

One row per raster tile.

| field | type | required | description |
|---|---|---:|---|
| `tile_id` | string | yes | Stable tile id, e.g. `sceneA_x003_y014_s256_o32` |
| `raster_id` | string | yes | Stable source raster id |
| `image_file_name` | string | yes | Relative path used in COCO `images.file_name` |
| `width` | int32 | yes | Tile width in pixels |
| `height` | int32 | yes | Tile height in pixels |
| `window_col_off` | int32 | yes | Source window column offset |
| `window_row_off` | int32 | yes | Source window row offset |
| `window_width` | int32 | yes | Source window width |
| `window_height` | int32 | yes | Source window height |
| `affine_a` | float64 | yes | Affine transform component |
| `affine_b` | float64 | yes | Affine transform component |
| `affine_c` | float64 | yes | Affine transform component |
| `affine_d` | float64 | yes | Affine transform component |
| `affine_e` | float64 | yes | Affine transform component |
| `affine_f` | float64 | yes | Affine transform component |
| `bounds_minx` | float64 | yes | Tile bounds in raster CRS |
| `bounds_miny` | float64 | yes | Tile bounds in raster CRS |
| `bounds_maxx` | float64 | yes | Tile bounds in raster CRS |
| `bounds_maxy` | float64 | yes | Tile bounds in raster CRS |
| `crs_wkt` | string | yes | Full CRS definition (WKT) |
| `crs_epsg` | int32 nullable | no | EPSG code if available |
| `split` | string | yes | `train/val/test` |

### 4.2 `annotation_index.parquet`

One row per COCO annotation polygon.

| field | type | required | description |
|---|---|---:|---|
| `coco_annotation_id` | int64 | yes | Annotation id in COCO |
| `coco_image_id` | int64 | yes | Image id in COCO |
| `tile_id` | string | yes | FK to `tile_index.tile_id` |
| `source_layer` | string | yes | Layer name from SHP/GPKG |
| `source_feature_id` | string | yes | Stable id from source feature |
| `category_id` | int32 | yes | COCO category id |
| `is_clipped` | bool | yes | Geometry clipped by tile border |
| `geom_type` | string | yes | `Polygon`/`MultiPolygon` |
| `area_px` | float64 | yes | Area in pixel space |
| `bbox_x` | float64 | yes | COCO bbox x |
| `bbox_y` | float64 | yes | COCO bbox y |
| `bbox_w` | float64 | yes | COCO bbox width |
| `bbox_h` | float64 | yes | COCO bbox height |

### 4.3 `source_features.parquet` (optional, for full lineage)

| field | type | required | description |
|---|---|---:|---|
| `source_feature_id` | string | yes | Source feature stable id |
| `source_layer` | string | yes | Original vector layer |
| `source_crs_wkt` | string | yes | CRS of source feature |
| `source_geom_wkb` | binary | yes | Original geometry |
| `attributes_json` | string | no | Selected source attributes |

### 4.4 `dataset_manifest.json`

```json
{
  "schema_version": "1.0.0",
  "created_at_utc": "2026-07-12T12:00:00Z",
  "pipeline_version": "0.1.0",
  "config": {
    "tile_size": 512,
    "tile_overlap": 64,
    "min_polygon_area_px": 10.0
  },
  "sources": [
    {
      "raster_id": "scene_001",
      "raster_path": "data/raw/scene_001.tif",
      "vector_path": "data/raw/labels.gpkg",
      "raster_sha256": "...",
      "vector_sha256": "..."
    }
  ],
  "outputs": {
    "coco_json": "data/processed/coco/instances_train.json",
    "tile_index": "data/processed/geo_index/tile_index.parquet",
    "annotation_index": "data/processed/geo_index/annotation_index.parquet"
  }
}
```

---

## 5) Function contracts (Python API)

Suggested public contracts for `src/geococo`.

```python
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import geopandas as gpd
import pandas as pd


@dataclass(frozen=True)
class DatasetConfig:
    tile_size: int
    tile_overlap: int
    min_polygon_area_px: float
    image_ext: str  # "tif" or "png" export target
    split_ratios: tuple[float, float, float]  # train, val, test
    class_map: dict[str, int]  # source class name -> coco category_id


@dataclass(frozen=True)
class RasterSource:
    raster_id: str
    raster_path: Path
    vector_path: Path
    vector_layer: str | None = None


@dataclass(frozen=True)
class TileRecord:
    tile_id: str
    raster_id: str
    image_file_name: str
    width: int
    height: int
    window_col_off: int
    window_row_off: int
    window_width: int
    window_height: int
    affine: tuple[float, float, float, float, float, float]
    bounds: tuple[float, float, float, float]
    crs_wkt: str
    crs_epsg: int | None
    split: str


@dataclass(frozen=True)
class CocoBuildResult:
    coco_json_path: Path
    images_count: int
    annotations_count: int
    categories_count: int
```

### 5.1 IO + CRS

```python
def load_raster_metadata(raster_path: Path) -> dict:
    """Return width, height, transform, bounds, CRS metadata."""


def load_vector(vector_path: Path, layer: str | None = None) -> gpd.GeoDataFrame:
    """Load vector labels from SHP/GPKG."""


def normalize_vector_to_raster_crs(
    vector_gdf: gpd.GeoDataFrame,
    raster_crs_wkt: str,
) -> gpd.GeoDataFrame:
    """Reproject vectors to raster CRS; raise on missing/invalid CRS."""
```

### 5.2 Tiling

```python
def generate_raster_tiles(
    source: RasterSource,
    cfg: DatasetConfig,
    images_out_dir: Path,
) -> pd.DataFrame:
    """
    Create raster tiles and return tile index DataFrame following `tile_index.parquet` schema.
    Must be deterministic for same input/config.
    """
```

### 5.3 Vector clipping + projection

```python
def build_tile_annotations(
    vector_gdf: gpd.GeoDataFrame,
    tile_index_df: pd.DataFrame,
    cfg: DatasetConfig,
) -> tuple[list[dict], pd.DataFrame]:
    """
    Return:
      - list of COCO annotation dictionaries
      - annotation_index DataFrame following `annotation_index.parquet` schema
    """
```

### 5.4 COCO export

```python
def build_coco_images(tile_index_df: pd.DataFrame) -> list[dict]:
    """Convert tile index to COCO `images` records with stable image ids."""


def build_coco_categories(class_map: dict[str, int]) -> list[dict]:
    """Build COCO `categories` list from configured class map."""


def export_coco_json(
    images: list[dict],
    annotations: list[dict],
    categories: list[dict],
    out_path: Path,
) -> CocoBuildResult:
    """Write COCO JSON and return export stats."""
```

### 5.5 Geo index export

```python
def export_geo_index(
    tile_index_df: pd.DataFrame,
    annotation_index_df: pd.DataFrame,
    out_dir: Path,
) -> dict[str, Path]:
    """Save `tile_index.parquet` and `annotation_index.parquet`, return output paths."""


def export_manifest(
    cfg: DatasetConfig,
    sources: Sequence[RasterSource],
    outputs: dict[str, Path],
    out_path: Path,
) -> Path:
    """Write `dataset_manifest.json` with versions, hashes, and parameter traceability."""
```

### 5.6 Inverse mapping (prediction -> source CRS)

```python
def restore_prediction_to_crs(
    tile_id: str,
    pred_segmentation_xy: list[float],
    tile_index_df: pd.DataFrame,
) -> "shapely.geometry.Polygon":
    """
    Convert one predicted polygon from tile pixel coordinates to source CRS coordinates
    using affine transform from tile index.
    """


def restore_predictions_batch(
    predictions_coco_json: Path,
    tile_index_path: Path,
    out_vector_path: Path,
    out_driver: str = "GPKG",
) -> Path:
    """Restore all predictions and save to GeoPackage/GeoJSON."""
```

---

## 6) Quality gates (must-have checks)

1. CRS checks
   - Every vector layer has CRS.
   - Vector CRS equals raster CRS after normalization.

2. Geometry checks
   - Invalid geometries repaired (`buffer(0)` or `make_valid`) before clipping.
   - Ignore empty or tiny polygons (`min_polygon_area_px`).

3. COCO checks
   - Unique ids for images/annotations.
   - Non-negative bbox sizes, non-empty segmentation.

4. Inverse mapping checks
   - Forward+inverse test on sample polygons has tolerance <= 0.5 px equivalent.

---

## 7) Main risks and mitigations

- CRS axis-order mismatch -> force explicit transformer behavior and test EPSG:4326 cases.
- Border duplicates due to overlap -> define dedup policy (e.g., keep polygon with max intersection area).
- SHP limitations -> use GPKG/GeoParquet internally, export SHP only if needed.
- I/O bottleneck with many tiles -> use Parquet indexes, optional COG, parallel tile workers.
- Non-deterministic ids -> deterministic ordering by `(raster_id, row_off, col_off, feature_id)`.
