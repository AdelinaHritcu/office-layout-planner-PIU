# Architecture Overview – Office Layout Planner

## Purpose
This document describes the main architecture of the **Office Layout Planner** project,
including the structure of UI components, scene management, and data persistence format.

---

## Project Structure

| Package                    | Description                                               |
|----------------------------|-----------------------------------------------------------|
| `office_layout/ui`         | Main user interface (windows, toolbar, sidebar, dialogs). |
| `office_layout/graphics`   | Canvas and 2D graphics scene.                             |
| `office_layout/models`     | Logical representation of the layout and object metadata. |
| `office_layout/algorithms` | Distance, routing, and validation algorithms.             |
| `office_layout/storage`    | JSON-based save/load implementation.                      |
| `resources`                | Visual assets and saved layouts.                          |

---

## JSON Layout Structure

The application stores and loads office layouts in `.json` format.
Each layout file contains metadata and a list of placed objects.

### Example

```json
{
  "layout_name": "Open Space A1",
  "canvas_size": { "width": 900, "height": 600 },
  "objects": [
    { "id": "desk_1", "type": "Desk", "x": 120, "y": 80, "width": 50, "height": 50, "rotation": 0 },
    { "id": "chair_1", "type": "Chair", "x": 120, "y": 140, "width": 30, "height": 30, "rotation": 0 }
  ],
  "metadata": {
    "author": "Adelina Hrițcu",
    "created_at": "2025-11-11T14:00:00",
    "description": "Example layout for open space area."
  }
}
