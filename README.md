# FjBa Basic Split Engine

**Version 1.2.1 | Basic Edition | QGIS**

A geospatial processing tool for splitting line datasets using polygon boundaries and transferring selected polygon attributes to the resulting line segments.

---

## Overview

The **FjBa Basic Split Engine** is a QGIS vector-processing tool designed to simplify line segmentation and polygon-based attribute assignment.

The tool processes multiple line layers and polygon layers, extracts polygon boundaries, splits line geometries at those boundaries, and assigns selected polygon attributes to the resulting line segments.

It features a custom graphical interface with FjBa metallic emerald and gold branding.

## Features

### Core geospatial processing

- Multiple line layer selection.
- Multiple polygon layer selection.
- Polygon geometry repair.
- Polygon boundary extraction.
- Line splitting using polygon boundaries.
- Merging of selected line layers.
- Merging of extracted polygon boundaries.
- Multipart-to-singlepart conversion.
- Spatial index optimization.
- Polygon attribute transfer.

### Attribute assignment

The engine uses the longest line intersection method to determine which polygon supplies the attributes for each resulting line segment.

Additional capabilities include:

- Selective polygon attribute transfer.
- Preservation of original attribute field definitions and types.
- Automatic output field naming.
- Handling of duplicate output field names.
- Attribute assignment independently for each source polygon layer.

### Graphical user interface

- Custom FjBa metallic emerald and gold branding.
- Animated metallic logo with light sweep.
- Resizable desktop window.
- Standard minimize, maximize and close buttons.
- Adaptive initial window dimensions.
- Laptop-friendly minimum window size.
- Scrollable interface.
- Layer selection panels.
- Attribute selection panel.
- Processing progress bar.
- Processing status information.
- Processing log.
- Cancellation request control.

---

## Processing Workflow

The Basic Split Engine follows this workflow:

1. **Select input layers**

   Select one or more line layers and one or more polygon layers from the current QGIS project.

2. **Select polygon attributes**

   Choose the polygon fields that should be transferred to the resulting line segments.

3. **Configure output**

   Enter the name of the output layer.

4. **Repair polygon geometries**

   The engine applies the native QGIS Fix Geometries algorithm to the selected polygon layers.

5. **Merge line layers**

   The selected line layers are merged and converted into single-part geometries.

6. **Extract polygon boundaries**

   Polygon boundaries are converted into line geometries and merged.

7. **Split line geometries**

   The merged line dataset is split using the extracted polygon boundaries.

8. **Build spatial indexes**

   Spatial indexes are constructed for the repaired polygon datasets to improve candidate-feature lookup.

9. **Transfer polygon attributes**

   For each resulting line segment, the engine identifies the intersecting polygon with the greatest intersection length in each relevant polygon layer.

10. **Create output**

    The resulting line features and transferred attributes are written to a temporary memory layer and added to the current QGIS project.

---

## Attribute Assignment Method

The attribute transfer process uses the length of the intersection between each resulting line segment and candidate polygon geometries.

The polygon with the greatest intersection length is selected as the winning polygon for the corresponding source polygon layer.

All selected attributes from that polygon layer are taken from the same winning feature.

When no suitable intersecting polygon is found, the corresponding transferred attribute values are left NULL.

For equal intersection lengths, the implementation uses sorted polygon feature IDs, so the first feature encountered wins.

---

## Output

The output is a temporary QGIS memory vector layer.

It contains:

- Original line attributes.
- Selected polygon attributes.
- Generated field names based on polygon layer names and source field names.
- Line geometries resulting from the splitting operation.

The output is automatically added to the current QGIS project after successful processing.

**Important:** Memory layers are temporary. Save or export the resulting layer to a permanent data source if it needs to be retained after closing the project or QGIS.

---

## Requirements

- QGIS with the PyQGIS API.
- QGIS Processing framework.
- Native QGIS Processing algorithms.
- Python and Qt versions supplied by the QGIS installation.

The source code uses `qgis.PyQt` to work with the Qt binding provided by QGIS.

The intended compatibility target is QGIS 3.x and QGIS 4.x. Actual compatibility must be verified against the specific releases before production deployment.

---

## Installation

The plugin packaging structure and QGIS plugin loader entry point must be prepared before distributing this script as a conventional installable QGIS plugin.

Once packaged:

1. Open QGIS.
2. Navigate to **Plugins → Manage and Install Plugins**.
3. Select the ZIP installation option if installing a locally packaged plugin.
4. Select the FjBa Basic Split Engine ZIP package.
5. Install and activate the plugin.
6. Launch the tool using its registered QGIS interface entry.

---

## Important Limitations

The Basic Edition uses synchronous processing.

Consequently:

- Large processing jobs may temporarily make QGIS less responsive.
- Cancellation is implemented as a processing cancellation request, not as a separate background worker.
- The output is created in memory rather than written directly to a permanent file.
- All selected input layers must use the same valid coordinate reference system.
- Actual processing performance depends on dataset size, geometry complexity, and available system resources.

Static code review and syntax validation do not replace testing with representative datasets inside each supported QGIS release.

---

## Processing Algorithms

The implementation uses the following native QGIS Processing algorithms:

| Algorithm | Purpose |
|---|---|
| `native:fixgeometries` | Repair polygon geometries |
| `native:mergevectorlayers` | Merge input vector layers |
| `native:multiparttosingleparts` | Convert multipart geometries |
| `native:polygonstolines` | Extract polygon boundaries |
| `native:splitwithlines` | Split line geometries |

Additional PyQGIS functionality is used for spatial indexing, geometry intersection analysis, feature creation, attribute transfer, and memory-layer management.

---

## Version History

### Version 1.2.1 – Basic Edition

- Multiple line layer selection.
- Multiple polygon layer selection.
- Polygon geometry repair.
- Polygon boundary extraction.
- Line splitting.
- Spatial indexing.
- Longest-intersection polygon assignment.
- Original attribute field definition preservation.
- Progress monitoring.
- Processing cancellation request.
- Processing log.
- Temporary memory output.
- Adaptive graphical interface.
- Animated FjBa metallic branding.
- Qt compatibility handling through `qgis.PyQt`.

---

## Credits

**FjBa – Geospatial Toolkit**

Basic Split Engine  
QGIS Vector Processing

---

## License

License information will be provided in the accompanying `LICENSE` file.

---

## Support and Feedback

For bug reports, suggestions, and technical feedback, please use the project's official repository and issue tracker once published.

**FjBa Basic Split Engine – Basic Edition**  
*Practical geospatial processing for QGIS.*
