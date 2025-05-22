from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import RadioButtons
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import os
import re

class DepthViewerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Depth-RGB Curator - v0.1.0")
        self.root.geometry("750x850")
        self.root.minsize(750, 850)  # Set minimum window size
        
        # Variables
        self.depth_array = None
        self.rgb_array = None
        self.current_colormap = "gray"
        self.available_colormaps = ["gray", "inferno", "viridis", "plasma", "magma", "cividis", "hot", "cool", "jet"]

        # Batch mode variables
        self.image_pairs = []  # List of (timestamp, rgb_path, depth_path) tuples
        self.current_pair_index = -1
        self.excluded_from_export = set()  # Set of indices excluded from export
        
        # Create main frame
        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create control panel
        self.control_frame = ttk.LabelFrame(self.main_frame, text="Controls")
        self.control_frame.pack(fill=tk.X, side=tk.TOP, pady=(0, 10))
        
        # Load buttons
        self.load_frame = ttk.Frame(self.control_frame)
        self.load_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.load_folder_btn = ttk.Button(self.load_frame, text="Load Images Folder", command=self.load_image_folder)
        self.load_folder_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.export_btn = ttk.Button(self.load_frame, text="Export All Depth Images", 
                                    command=self.export_images, state=tk.DISABLED)
        self.export_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.toggle_btn = ttk.Button(self.load_frame, text="Exclude from Export", 
                                   command=self.toggle_exclusion, state=tk.DISABLED)
        self.toggle_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.selection_label = ttk.Label(self.load_frame, text="0 images excluded")
        self.selection_label.pack(side=tk.LEFT)
        
        # Navigation buttons (initially disabled)
        self.nav_frame = ttk.Frame(self.control_frame)
        self.nav_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.prev_btn = ttk.Button(self.nav_frame, text="Previous Image (←)", command=self.prev_image, state=tk.DISABLED)
        self.prev_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.next_btn = ttk.Button(self.nav_frame, text="Next Image (→)", command=self.next_image, state=tk.DISABLED)
        self.next_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.image_label = ttk.Label(self.nav_frame, text="No images loaded")
        self.image_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # Colormap selection
        self.colormap_frame = ttk.Frame(self.control_frame)
        self.colormap_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Label(self.colormap_frame, text="Colormap:").pack(side=tk.LEFT, padx=(0, 10))
        
        self.colormap_var = tk.StringVar(value=self.current_colormap)
        self.colormap_combo = ttk.Combobox(self.colormap_frame, textvariable=self.colormap_var, 
                                          values=self.available_colormaps, state="readonly", width=15)
        self.colormap_combo.pack(side=tk.LEFT)
        self.colormap_combo.bind("<<ComboboxSelected>>", self.update_colormap)
        
        # Create figure frame
        self.figure_frame = ttk.Frame(self.main_frame)
        self.figure_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create matplotlib figure
        self.fig = Figure(figsize=(10, 8))
        self.ax1 = self.fig.add_subplot(211)
        self.ax2 = self.fig.add_subplot(212)
        
        # Embed figure in tkinter window
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.figure_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Add toolbar
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.figure_frame)
        self.toolbar.update()
        
        # Initialize plot elements
        self.depth_img = None
        self.rgb_img = None
        self.text = self.ax1.text(0.05, 0.95, '', transform=self.ax1.transAxes, color='white', fontsize=12,
                             bbox=dict(facecolor='black', alpha=0.5))
        self.crosshair, = self.ax2.plot([], [], 'r+', markersize=10, markeredgewidth=2)
        
        # Exclusion indicator (will be positioned in update_plots)
        self.exclusion_text = None
        
        # Connect mouse events
        self.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)
        
        # Bind keyboard events for navigation at the root level
        self.root.bind('<Left>', lambda event: self.prev_image())
        self.root.bind('<Right>', lambda event: self.next_image())
        self.root.bind('<space>', lambda event: self.handle_space_key(event))
        
        # Bind to figure canvas click to ensure proper focus
        self.canvas.mpl_connect('button_press_event', self.on_canvas_click)
        
        # Initial setup
        self.setup_axes()
        
        # Show keyboard shortcuts
        self.show_keyboard_shortcuts()

    def on_canvas_click(self, event):
        """Handle clicks on the canvas to ensure focus returns to the main window"""
        # This ensures the root window has focus for keyboard events
        self.root.focus_set()

    def handle_space_key(self, event):
        """Handle space key press with focus awareness"""
        # Check if the event's widget is a button (which would handle its own space key)
        if isinstance(event.widget, ttk.Button) or isinstance(event.widget, tk.Button):
            return  # Let the button handle its own space key
        
        # Otherwise toggle exclusion
        self.toggle_exclusion()
        return "break"  # Prevent further handling of this event

    def show_keyboard_shortcuts(self):
        """Show a message with keyboard shortcuts"""
        shortcuts = (
            "Keyboard Shortcuts:\n"
            "→ (Right Arrow): Next image\n"
            "← (Left Arrow): Previous image\n"
            "Space: Toggle exclusion status"
        )
        messagebox.showinfo("Keyboard Shortcuts", shortcuts)

    def toggle_exclusion(self):
        """Toggle exclusion of current image from export"""
        if self.current_pair_index < 0 or not self.image_pairs:
            return
            
        if self.current_pair_index in self.excluded_from_export:
            self.excluded_from_export.remove(self.current_pair_index)
        else:
            self.excluded_from_export.add(self.current_pair_index)
            
        # Update counter
        self.selection_label.config(text=f"{len(self.excluded_from_export)} images excluded")
        
        # Update display to show exclusion status
        self.update_plots()

    def load_image_folder(self):
        """Load a folder of image pairs with matching timestamps"""
        folder_path = filedialog.askdirectory(title="Select folder with RGB and depth images")
        if not folder_path:
            return

        try:
            # Get all files in the directory
            all_files = os.listdir(folder_path)
            
            # Find RGB and depth pairs
            rgb_files = [f for f in all_files if f.endswith("_image.jpg")]
            depth_files = [f for f in all_files if f.endswith("_depth.tiff")]
            
            # Extract timestamps and match pairs
            image_pairs = []
            
            for rgb_file in rgb_files:
                # Extract timestamp from filename (e.g., 1747910207.067782_image.jpg)
                match = re.match(r"^([\d.]+)_image\.jpg$", rgb_file)
                if match:
                    timestamp = match.group(1)
                    depth_file = f"{timestamp}_depth.tiff"
                    
                    if depth_file in depth_files:
                        rgb_path = os.path.join(folder_path, rgb_file)
                        depth_path = os.path.join(folder_path, depth_file)
                        image_pairs.append((timestamp, rgb_path, depth_path))
            
            # Sort by timestamp
            image_pairs.sort(key=lambda x: float(x[0]))
            
            if not image_pairs:
                messagebox.showinfo("No Matching Pairs", "No matching RGB/depth image pairs found in the selected folder.")
                return
                
            # Store the pairs and reset index
            self.image_pairs = image_pairs
            self.current_pair_index = -1
            
            # Clear exclusions - all images are included by default
            self.excluded_from_export = set()
            self.selection_label.config(text="0 images excluded")
            
            # Enable navigation and selection buttons
            self.prev_btn.config(state=tk.NORMAL)
            self.next_btn.config(state=tk.NORMAL)
            self.toggle_btn.config(state=tk.NORMAL)
            self.export_btn.config(state=tk.NORMAL)
            
            # Load the first image pair
            self.next_image()
            
            # Make sure root has focus for keyboard shortcuts
            self.root.focus_set()
            
            messagebox.showinfo("Success", f"Found {len(image_pairs)} RGB/depth image pairs. All are selected for export by default.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image folder: {str(e)}")

    def next_image(self):
        """Load the next image pair in the batch"""
        if not self.image_pairs or self.next_btn['state'] == tk.DISABLED:
            return
            
        # Move to next pair (or wrap around to first pair)
        self.current_pair_index = (self.current_pair_index + 1) % len(self.image_pairs)
        self.load_current_pair()
        
        # Make sure root has focus for keyboard shortcuts
        self.root.focus_set()
        
    def prev_image(self):
        """Load the previous image pair in the batch"""
        if not self.image_pairs or self.prev_btn['state'] == tk.DISABLED:
            return
            
        # Move to previous pair (or wrap around to last pair)
        self.current_pair_index = (self.current_pair_index - 1) % len(self.image_pairs)
        self.load_current_pair()
        
        # Make sure root has focus for keyboard shortcuts
        self.root.focus_set()
        
    def load_current_pair(self):
        """Load the current image pair based on the index"""
        if 0 <= self.current_pair_index < len(self.image_pairs):
            timestamp, rgb_path, depth_path = self.image_pairs[self.current_pair_index]
            
            # Update image label with export status
            status = " [EXCLUDED]" if self.current_pair_index in self.excluded_from_export else ""
            self.image_label.config(text=f"Image {self.current_pair_index + 1} of {len(self.image_pairs)} - Timestamp: {timestamp}{status}")
            
            # Load depth image
            try:
                depth_img = Image.open(depth_path)
                self.depth_array = np.array(depth_img)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load depth image: {str(e)}")
                return
                
            # Load RGB image
            try:
                rgb_img = Image.open(rgb_path).convert("RGB")
                # Resize to match depth image dimensions
                rgb_img = rgb_img.resize((self.depth_array.shape[1], self.depth_array.shape[0]), Image.BILINEAR)
                self.rgb_array = np.array(rgb_img)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load RGB image: {str(e)}")
                return
            
            # Update plots
            self.update_plots()
        
    def setup_axes(self):
        self.ax1.set_title("Depth Map – hover to see value")
        self.ax1.axis('off')
        
        self.ax2.set_title("RGB Image – shows cursor position")
        self.ax2.axis('off')
        
        self.fig.tight_layout()
        self.canvas.draw()
    
    def update_colormap(self, event=None):
        self.current_colormap = self.colormap_var.get()
        self.update_plots()
    
    def update_plots(self):
        # Clear axes
        self.ax1.clear()
        self.ax2.clear()
        
        # Update depth plot if data available
        if self.depth_array is not None:
            # Normalize depth values for display
            depth_display = (self.depth_array - np.min(self.depth_array)) / (np.max(self.depth_array) - np.min(self.depth_array))
            self.depth_img = self.ax1.imshow(depth_display, cmap=self.current_colormap)
            self.ax1.set_title(f"Depth Map ({self.current_colormap}) – hover to see value")
            
            # Add exclusion indicator if this image is excluded - centered on depth image
            if self.current_pair_index in self.excluded_from_export:
                # Get the dimensions of the depth image
                height, width = self.depth_array.shape
                x_center = width / 2
                y_center = height / 2
                
                # Create a semi-transparent red overlay across the entire depth image
                overlay = np.zeros((height, width, 4))  # RGBA
                overlay[:, :, 0] = 1.0  # Red channel
                overlay[:, :, 3] = 0.3  # Alpha channel (transparency)
                self.ax1.imshow(overlay, extent=[0, width, height, 0], interpolation='nearest')
                
                # Add text centered on the depth image in data coordinates
                self.exclusion_text = self.ax1.text(x_center, y_center, 'EXCLUDED FROM EXPORT', 
                                                  color='white', fontsize=24, fontweight='bold',
                                                  ha='center', va='center',
                                                  bbox=dict(facecolor='red', alpha=0.7, boxstyle='round,pad=0.5'))
        else:
            self.ax1.set_title("Depth Map – No data loaded")
        
        # Update RGB plot if data available
        if self.rgb_array is not None:
            self.rgb_img = self.ax2.imshow(self.rgb_array)
            self.ax2.set_title("RGB Image – shows cursor position")
        else:
            self.ax2.set_title("RGB Image – No data loaded")
        
        # Reset text and crosshair
        self.text = self.ax1.text(0.05, 0.95, '', transform=self.ax1.transAxes, color='white', fontsize=12,
                             bbox=dict(facecolor='black', alpha=0.5))
        self.crosshair, = self.ax2.plot([], [], 'r+', markersize=10, markeredgewidth=2)
        
        # Turn off axes
        self.ax1.axis('off')
        self.ax2.axis('off')
        
        self.fig.tight_layout()
        self.canvas.draw()
    
    def on_mouse_move(self, event):
        try:
            if event.inaxes == self.ax1 and self.depth_array is not None:
                col = int(event.xdata + 0.5)
                row = int(event.ydata + 0.5)

                if 0 <= col < self.depth_array.shape[1] and 0 <= row < self.depth_array.shape[0]:
                    z = self.depth_array[row, col]
                    self.text.set_text(f"X: {col}, Y: {row}, Depth: {z}")
                    self.crosshair.set_data([col], [row])
                else:
                    self.text.set_text('')
                    self.crosshair.set_data([], [])

                self.canvas.draw_idle()
        except:
            pass
    
    def export_images(self):
        """Export all depth TIFF images except those that have been excluded"""
        if not self.image_pairs:
            messagebox.showinfo("No Images", "Please load images first")
            return
        
        # Ask for export directory
        export_dir = filedialog.askdirectory(title="Select Export Directory")
        if not export_dir:
            return  # User canceled
        
        try:
            exported_count = 0
            
            # Iterate through all pairs and export those not excluded
            for idx, (timestamp, _, depth_path) in enumerate(self.image_pairs):
                if idx not in self.excluded_from_export:
                    # Load the depth image
                    depth_img = Image.open(depth_path)
                    
                    # Save as original format
                    output_path = f"{export_dir}/{timestamp}_depth.tiff"
                    depth_img.save(output_path)
                    exported_count += 1
            
            # Calculate how many were excluded
            excluded_count = len(self.excluded_from_export)
            total_count = len(self.image_pairs)
            
            messagebox.showinfo("Export Complete", 
                               f"Exported {exported_count} depth images to {export_dir}\n"
                               f"Excluded: {excluded_count}\n"
                               f"Total images: {total_count}")
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export images: {str(e)}")

# Main application entry point
if __name__ == "__main__":
    root = tk.Tk()
    app = DepthViewerApp(root)
    root.mainloop()
