"""
crop_plants.py

Uses YOLO labels to crop each plant from the original images and saves the
cropped images into the correct MobileNet directory structure.

Expected input structure:
potted_plant_dataset/
├── images/
│   ├── train/
│   └── valid/
└── labels/
    ├── train/
    └── valid/

Expected output structure:
cropped_dataset/
├── train/
│   ├── succulent/
│   ├── cactus/
│   ├── green_plant/
│   ├── leafy_plant/
│   ├── lillies/
│   └── lavender/
└── val/
    ├── succulent/
    ├── cactus/
    ├── green_plant/
    ├── leafy_plant/
    ├── lillies/
    └── lavender/

This script determines the plant type from the filename prefix.
Example:
    succulent_001.jpg  -> succulent
    cactus_12.png      -> cactus
    leafy_plant_45.jpg -> leafy_plant
"""

from pathlib import Path
from PIL import Image

# -------------------------------------------------------------------
# CONFIGURATION
# -------------------------------------------------------------------

YOLO_ROOT = Path("yolov8/datasets/potted_plant_detection_dataset")
OUTPUT_ROOT = Path("cropped_dataset")

# Map YOLO folder names to MobileNet folder names
SPLIT_MAP = {
    "train": "train",
    "valid": "val",   # YOLO uses "valid", output uses "val"
}

# All plant types
PLANT_TYPES = [
    "succulent",
    "cactus",
    "green",
    "leafy",
    "lillies",
    "lavender",
]

# Optional padding around the crop in pixels
PADDING = 5

# Supported image extensions
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}


# -------------------------------------------------------------------
# HELPER FUNCTIONS
# -------------------------------------------------------------------

def detect_plant_type(filename_stem: str):
    """
    Determine which plant type appears in the filename.
    Longest names are checked first so 'green_plant'
    matches before 'plant'.
    """
    for plant in sorted(PLANT_TYPES, key=len, reverse=True):
        if filename_stem.startswith(plant):
            return plant
    return None


def create_output_dirs():
    for split in SPLIT_MAP.values():
        for plant in PLANT_TYPES:
            (OUTPUT_ROOT / split / plant).mkdir(parents=True, exist_ok=True)


def crop_image(image_path: Path, label_path: Path, output_dir: Path):
    plant_type = detect_plant_type(image_path.stem)

    if plant_type is None:
        print(f"Could not determine plant type from filename: {image_path.name}")
        return

    try:
        img = Image.open(image_path).convert("RGB")
    except Exception as e:
        print(f"Failed to open {image_path}: {e}")
        return

    img_width, img_height = img.size

    with open(label_path, "r") as f:
        lines = f.readlines()

    # Handle multiple detections if present
    for i, line in enumerate(lines):
        parts = line.strip().split()
        if len(parts) != 5:
            continue

        _, x_center, y_center, width, height = parts

        x_center = float(x_center) * img_width
        y_center = float(y_center) * img_height
        width = float(width) * img_width
        height = float(height) * img_height

        x1 = int(x_center - width / 2) - PADDING
        y1 = int(y_center - height / 2) - PADDING
        x2 = int(x_center + width / 2) + PADDING
        y2 = int(y_center + height / 2) + PADDING

        # Clamp to image boundaries
        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(img_width, x2)
        y2 = min(img_height, y2)

        if x2 <= x1 or y2 <= y1:
            continue

        crop = img.crop((x1, y1, x2, y2))

        # Save to correct class folder
        save_dir = output_dir / plant_type
        save_path = save_dir / f"{image_path.stem}_{i}.jpg"
        crop.save(save_path, quality=95)


# -------------------------------------------------------------------
# MAIN PROCESSING
# -------------------------------------------------------------------

def main():
    create_output_dirs()

    for input_split, output_split in SPLIT_MAP.items():
        images_dir = YOLO_ROOT / "images" / input_split
        labels_dir = YOLO_ROOT / "labels" / input_split
        output_dir = OUTPUT_ROOT / output_split

        if not images_dir.exists():
            print(f"Missing directory: {images_dir}")
            continue

        for image_path in images_dir.iterdir():
            if image_path.suffix.lower() not in IMAGE_EXTENSIONS:
                continue

            label_path = labels_dir / f"{image_path.stem}.txt"
            if not label_path.exists():
                print(f"Missing label for {image_path.name}")
                continue

            crop_image(image_path, label_path, output_dir)

    print("\nDone.")
    print(f"Cropped images saved to: {OUTPUT_ROOT.resolve()}")


if __name__ == "__main__":
    main()