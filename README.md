# Depth-RGB Dataset Curator

## Description
The Depth-RGB Dataset Curator is a tool designed to facilitate the management and processing of paired RGB and depth images. It allows users to load, view, and export depth images while providing options to exclude certain images from export. The application is optimized for use with depth maps captured using the **LiDAR Depth Map Capture for iOS** app, ensuring high-quality data processing.

## Requirements
- Python
- PIL
- NumPy
- Matplotlib
- Tkinter

## Quick Start
```bash
# Clone the repository
git clone https://github.com/Jakub-Espandr/depth-rgb-dataset-curator.git
# Move to the directory
cd depth-rgb-dataset-curator
# Install dependencies
pip install -r requirements.txt
# Run the application
python curator.py
```

## Usage
1. Run the application:
   ```bash
   python curator.py
   ```
2. Use the "Load Images Folder" button to select a directory containing your RGB and depth images.
3. Navigate through images using the arrow keys:
   - Right Arrow (→): Next image
   - Left Arrow (←): Previous image
   - Space: Toggle exclusion status
4. Export images using the "Export All Depth Images" button.

## Features
- Load and view paired RGB and depth images.
- Navigate through image pairs using keyboard shortcuts.
- Exclude specific images from export.
- Export depth images to a selected directory.
- Supports various colormaps for depth visualization.

## How It Works
The application:
1. Loads RGB and depth image pairs from a selected directory.
2. Allows navigation through image pairs with keyboard shortcuts.
3. Provides options to exclude images from export.
4. Exports selected depth images to a user-defined directory.

## Output Format
The exported depth images are saved in their original TIFF format, preserving the original precision and quality.

## Sample Data

Sample data is available in the `Test` folder. This data can be used to test the application's functionality and ensure that it is working as expected. The sample data includes paired RGB and depth images with matching timestamps, organized in the correct directory structure for easy loading and processing.

## Notes
- Ensure that the RGB and depth images are named with matching timestamps for proper pairing.
- The application supports various colormaps for depth visualization.

## Data Source
The RGB and depth images used in this application should be captured using compatible devices and software that support depth map generation. Recommended tools include:

- **LiDAR Depth Map Capture for iOS**: [LiDAR Depth Map Capture for iOS](https://github.com/ioridev/LiDAR-Depth-Map-Capture-for-iOS)
This app allows for capturing full-resolution, 32-bit floating-point depth maps using the LiDAR scanner on supported iPhone and iPad models. The depth maps preserve the original precision, making them suitable for high-quality processing.

Ensure that both RGB and depth images are stored in the same directory with matching timestamps for proper pairing. When sharing data, include the entire output folder containing both image types to maintain the correct structure.

## License
This project is licensed under the MIT License.