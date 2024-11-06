import os
import random
import json
import shutil

from PIL import Image, ImageTk, ImageDraw, ImageFont
from pycocotools.coco import COCO
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox

# Initialize customtkinter
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class CocoDatasetGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("COCO-Style Dataset Doctor")
        self.geometry("1700x1000")  # Increased width to accommodate textboxes

        # Initialize dataset variables
        self.coco = None
        self.image_folder = None
        self.image_ids = []
        self.current_index = 0
        self.annotation_file = None  # Store the original annotation file path

        self.dataset_info = "<INFO PLACEHOLDER>"

        # Class colors
        self.class_colors = {}
        self.classes = []

        # Image ID to file path mapping
        self.image_id_to_path = {}

        # Load recent paths
        self.recent_paths = {}
        self.load_recent_paths()

        # Setup GUI elements
        self.setup_gui()

        # Attempt to load dataset if recent paths are available
        if (
            "annotation_file" in self.recent_paths
            and "image_folder" in self.recent_paths
        ):
            try:
                self.load_dataset_from_paths(
                    self.recent_paths["annotation_file"],
                    self.recent_paths["image_folder"],
                )
            except Exception as e:
                print(f"Failed to load recent dataset: {e}")

    def setup_gui(self):
        """Set up the main GUI components."""
        self.create_main_frames()
        self.create_navigation_buttons()
        self.create_content_area()
        self.create_bottom_info_area()
        self.create_control_buttons()

    def create_main_frames(self):
        """Create the main frames for the GUI."""
        # Main frame
        self.frame = ctk.CTkFrame(master=self)
        self.frame.pack(pady=10, padx=10, fill="both", expand=True)

        # Top frame for navigation and image info
        self.top_frame = ctk.CTkFrame(master=self.frame)
        self.top_frame.pack(pady=5, padx=5, fill="x")

    def create_navigation_buttons(self):
        """Create navigation buttons for image browsing."""
        # Image index label
        self.image_index_label = ctk.CTkLabel(master=self.top_frame, text="Image 0/0")
        self.image_index_label.pack(side="left", padx=10)

        # Navigation buttons frame
        self.nav_frame = ctk.CTkFrame(master=self.top_frame)
        self.nav_frame.pack(side="right", padx=10)

        # Previous sample button
        self.prev_button = ctk.CTkButton(
            master=self.nav_frame, text="Previous Sample", command=self.prev_sample
        )
        self.prev_button.grid(row=0, column=0, padx=5)

        # Next sample button
        self.next_button = ctk.CTkButton(
            master=self.nav_frame, text="Next Sample", command=self.next_sample
        )
        self.next_button.grid(row=0, column=1, padx=5)

    def create_content_area(self):
        """Create the main content area for displaying images and annotations."""
        # Main content frame with three columns (image info, image, and annotation info)
        self.content_frame = ctk.CTkFrame(master=self.frame)
        self.content_frame.pack(pady=10, padx=10, fill="both", expand=True)

        # Image display label in the center
        self.image_label = ctk.CTkLabel(master=self.content_frame, text="")
        self.image_label.pack(side="left", padx=10, pady=10)

        # Left Textbox for Image Info (non-scrollable)
        self.image_info_textbox = ctk.CTkTextbox(
            master=self.content_frame, width=400, height=400
        )
        self.image_info_textbox.pack(side="left", padx=10, pady=5)
        self.image_info_textbox.configure(state="disabled")

        # Right Textbox for Annotation Info (scrollable)
        self.annotation_textbox = ctk.CTkTextbox(
            master=self.content_frame, width=400, height=400
        )
        self.annotation_textbox.pack(side="left", padx=10, pady=5)
        self.annotation_textbox.configure(state="disabled")

    def create_bottom_info_area(self):
        """Create the bottom area for class list and dataset info."""
        # Bottom frame for class list and info
        self.bottom_frame = ctk.CTkFrame(master=self.frame)
        self.bottom_frame.pack(pady=5, padx=5, fill="x")

        # Classes textbox
        self.classes_textbox = ctk.CTkTextbox(master=self.bottom_frame, width=200)
        self.classes_textbox.pack(side="left", padx=10, pady=5)
        self.classes_textbox.configure(state="disabled")

        # Dataset info textbox
        self.info_textbox = ctk.CTkTextbox(master=self.bottom_frame, height=100)
        self.info_textbox.pack(side="left", padx=10, pady=5, fill="x", expand=True)
        self.info_textbox.configure(state="disabled")

    def create_control_buttons(self):
        """Create control buttons for various dataset operations."""
        # Control buttons frame
        self.control_frame = ctk.CTkFrame(master=self.frame)
        self.control_frame.pack(pady=10, padx=10, fill="x")

        # Load Dataset button
        self.load_dataset_button = ctk.CTkButton(
            master=self.control_frame,
            text="Load Dataset",
            command=self.load_dataset,
        )
        self.load_dataset_button.pack(side="left", padx=10)

        # Merge Dataset button
        self.merge_dataset_button = ctk.CTkButton(
            master=self.control_frame,
            text="Merge Dataset",
            command=self.add_dataset,
        )
        self.merge_dataset_button.pack(side="left", padx=10)

        # Button to manage classes
        self.manage_classes_button = ctk.CTkButton(
            master=self.control_frame,
            text="Manage Class IDs",
            command=self.manage_classes,
        )
        self.manage_classes_button.pack(side="left", padx=10)

        # Subsample button
        self.increase_decrease_button = ctk.CTkButton(
            master=self.control_frame,
            text="Sub/Over Sample Dataset",
            command=self.sub_or_over_sample_dataset,
        )
        self.increase_decrease_button.pack(side="left", padx=10)

        # Add 'iscrowd' field button
        self.add_missing_is_crowd_field_button = ctk.CTkButton(
            master=self.control_frame,
            text="Add Missing 'iscrowd' Field",
            command=self.add_missing_is_crowd_field,
        )
        self.add_missing_is_crowd_field_button.pack(side="left", padx=10)

        # Add 'iscrowd' field button
        self.add_missing_is_crowd_field_button = ctk.CTkButton(
            master=self.control_frame,
            text="Add Missing 'segmentation' Field",
            command=self.add_missing_segmentation_field,
        )
        self.add_missing_is_crowd_field_button.pack(side="left", padx=10)

        # Export Modified Annotations button
        self.export_annotations_button = ctk.CTkButton(
            master=self.control_frame,
            text="Export Modified Annotations",
            command=self.export_modified_annotations,
        )
        self.export_annotations_button.pack(side="left", padx=10)

        # Export Dataset button
        self.export_dataset_button = ctk.CTkButton(
            master=self.control_frame,
            text="Export Dataset",
            command=self.export_dataset,
        )
        self.export_dataset_button.pack(side="left", padx=10)

        # Delete Current Image button
        self.delete_image_button = ctk.CTkButton(
            master=self.control_frame,
            text="Delete Current Image",
            command=self.delete_current_image,
            fg_color="red",
        )
        self.delete_image_button.pack(side="left", padx=10)

    def load_recent_paths(self):
        """Load recent paths from a JSON file."""
        try:
            with open("recent_paths.json", "r") as f:
                self.recent_paths = json.load(f)
        except Exception as e:
            print(f"No recent paths found: {e}")
            self.recent_paths = {}

    def save_recent_paths(self):
        """Save recent paths to a JSON file."""
        try:
            with open("recent_paths.json", "w") as f:
                json.dump(self.recent_paths, f)
        except Exception as e:
            print(f"Failed to save recent paths: {e}")

    def load_dataset(self):
        """Load dataset by selecting annotation file and image folder."""
        # Get recent annotation file and image folder
        recent_annotation_file = self.recent_paths.get("annotation_file", "")
        recent_image_folder = self.recent_paths.get("image_folder", "")

        # File dialog to select annotation file
        annotation_file = filedialog.askopenfilename(
            title="Select COCO Annotation File",
            filetypes=[("JSON Files", "*.json")],
            initialdir=(
                os.path.dirname(recent_annotation_file)
                if recent_annotation_file
                else ""
            ),
            initialfile=(
                os.path.basename(recent_annotation_file)
                if recent_annotation_file
                else ""
            ),
        )
        if not annotation_file:
            messagebox.showerror("Error", "No annotation file selected.")
            return

        # Directory dialog to select image folder
        image_folder = filedialog.askdirectory(
            title="Select COCO Image Folder",
            initialdir=recent_image_folder if recent_image_folder else "",
        )
        if not image_folder:
            messagebox.showerror("Error", "No image folder selected.")
            return

        self.load_dataset_from_paths(annotation_file, image_folder)

    def load_dataset_from_paths(self, annotation_file, image_folder):
        """Load dataset from given annotation file and image folder paths."""
        try:
            self.coco = COCO(annotation_file)
            self.annotation_file = annotation_file
            self.image_folder = image_folder
            self.image_ids = self.coco.getImgIds()
            self.current_index = 0

            # Map image IDs to file paths
            self.image_id_to_path = {}
            for img_info in self.coco.loadImgs(self.image_ids):
                image_path = os.path.join(self.image_folder, img_info["file_name"])
                self.image_id_to_path[img_info["id"]] = image_path

            # Get list of classes
            self.classes = [
                cat["name"] for cat in self.coco.loadCats(self.coco.getCatIds())
            ]
            self.assign_class_colors()

            # Update dataset information
            self.update_info_textbox()
            self.update_classes_textbox()
            self.update_image_index_label()

            # Display the first image and annotations
            self.display_sample(self.current_index)

            # Save recent paths
            self.recent_paths["annotation_file"] = annotation_file
            self.recent_paths["image_folder"] = image_folder
            self.save_recent_paths()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load dataset: {e}")

    def assign_class_colors(self):
        """Assign random colors to each class."""
        random.seed(42)  # For reproducibility
        for cat_id in self.coco.getCatIds():
            self.class_colors[cat_id] = (
                random.randint(0, 255),
                random.randint(0, 255),
                random.randint(0, 255),
            )

    def delete_current_image(self):
        """Delete the current image and its annotations from the dataset."""
        if not self.image_ids:
            return

        # Ask for confirmation
        result = messagebox.askyesno(
            "Confirm Deletion", "Are you sure you want to delete the current image?"
        )
        if not result:
            return

        # Get the image ID and remove it from the dataset
        current_image_id = self.image_ids[self.current_index]

        # Remove image from dataset
        self.coco.dataset["images"] = [
            img for img in self.coco.dataset["images"] if img["id"] != current_image_id
        ]

        # Remove annotations for the current image
        self.coco.dataset["annotations"] = [
            ann
            for ann in self.coco.dataset["annotations"]
            if ann["image_id"] != current_image_id
        ]

        # Remove the image from image_ids and image_id_to_path
        del self.image_id_to_path[current_image_id]
        del self.image_ids[self.current_index]

        # If there are no more images, reset the display
        if not self.image_ids:
            messagebox.showinfo("Info", "No more images in the dataset.")
            self.reset_display()
            return

        # Adjust the current index if necessary
        if self.current_index >= len(self.image_ids):
            self.current_index = len(self.image_ids) - 1

        # Rebuild the index after deletion
        self.coco.createIndex()

        # Update the display
        self.update_info_textbox()
        self.display_sample(self.current_index)

    def reset_display(self):
        """Reset the display when no images are available."""
        self.image_label.configure(image="")
        self.image_index_label.configure(text="Image 0/0")
        self.dataset_info = ""
        self.info_textbox.configure(state="normal")
        self.info_textbox.delete("1.0", tk.END)
        self.info_textbox.configure(state="disabled")

    def update_info_textbox(self):
        """Update the dataset information textbox."""
        num_total_annotations = len(self.coco.dataset["annotations"])
        num_images = len(self.coco.dataset["images"])

        self.dataset_info = f"Number of images: {num_images}\n"
        self.dataset_info += f"Number of annotations: {num_total_annotations}\n"

        self.info_textbox.configure(state="normal")
        self.info_textbox.delete("1.0", tk.END)
        self.info_textbox.insert("1.0", self.dataset_info)
        self.info_textbox.configure(state="disabled")

    def update_classes_textbox(self):
        """Update the classes textbox with the list of classes."""
        self.classes_textbox.configure(state="normal")
        self.classes_textbox.delete("1.0", tk.END)
        self.classes_textbox.insert("1.0", "Class Name (ID):\n")
        for cat_id in sorted(self.coco.getCatIds()):
            cat = self.coco.loadCats(cat_id)[0]
            cat_name = cat["name"]
            self.classes_textbox.insert(tk.END, f"{cat_name} ({cat_id})\n")
        self.classes_textbox.configure(state="disabled")

    def update_image_index_label(self):
        """Update the image index label."""
        if self.image_ids:
            self.image_index_label.configure(
                text=f"Image {self.current_index + 1}/{len(self.image_ids)}"
            )
        else:
            self.image_index_label.configure(text="Image 0/0")

    def display_sample(self, index):
        """Display the image and annotations at the given index."""
        if not self.image_ids:
            return

        # Get image info
        img_info = self.coco.loadImgs(self.image_ids[index])[0]
        image_id = img_info["id"]
        image_path = self.image_id_to_path.get(image_id)

        # Display image info
        self.display_image_info(img_info)

        # Open and display image with annotations
        self.display_image_with_annotations(img_info, image_path)

        # Update image index label
        self.update_image_index_label()

    def display_image_info(self, img_info):
        """Display image information in the textbox."""
        self.image_info_textbox.configure(state="normal")
        self.image_info_textbox.delete("1.0", tk.END)
        self.image_info_textbox.insert(tk.END, json.dumps(img_info, indent=4))
        self.image_info_textbox.configure(state="disabled")

    def display_image_with_annotations(self, img_info, image_path):
        """Display the image with drawn annotations."""
        try:
            image = Image.open(image_path).convert("RGB")
        except FileNotFoundError:
            messagebox.showerror("Error", f"Image file not found: {image_path}")
            return

        # Draw annotations on the image
        self.draw_annotations_on_image(image, img_info["id"])

        # Resize and display the image
        image.thumbnail((800, 600))
        self.photo = ImageTk.PhotoImage(image)
        self.image_label.configure(image=self.photo)
        self.image_label.image = self.photo

    def draw_annotations_on_image(self, image, image_id):
        """Draw annotations on the image."""
        ann_ids = self.coco.getAnnIds(imgIds=image_id)
        anns = self.coco.loadAnns(ann_ids)
        draw = ImageDraw.Draw(image)
        font = ImageFont.load_default()

        for ann in anns:
            bbox = ann["bbox"]
            x, y, w, h = bbox
            cat_id = ann["category_id"]
            color = self.class_colors.get(cat_id, (255, 0, 0))
            outline_color = tuple(color)
            draw.rectangle([x, y, x + w, y + h], outline=outline_color, width=2)

            category_name = self.coco.loadCats(cat_id)[0]["name"]

            label = f"{category_name}"

            # Calculate text size
            text_bbox = draw.textbbox((x, y), label, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]

            # Draw label rectangle
            text_bg_rect = [x, y, x + text_width + 4, y + text_height + 4]
            draw.rectangle(text_bg_rect, fill=outline_color)

            # Draw text
            draw.text((x + 2, y + 2), label, fill="black", font=font)

        # Display annotations in the right textbox
        self.annotation_textbox.configure(state="normal")
        self.annotation_textbox.delete("1.0", tk.END)
        self.annotation_textbox.insert(tk.END, json.dumps(anns, indent=4))
        self.annotation_textbox.configure(state="disabled")

    def next_sample(self):
        """Display the next image in the dataset."""
        if not self.image_ids:
            return
        self.current_index = (self.current_index + 1) % len(self.image_ids)
        self.display_sample(self.current_index)

    def prev_sample(self):
        """Display the previous image in the dataset."""
        if not self.image_ids:
            return
        self.current_index = (self.current_index - 1) % len(self.image_ids)
        self.display_sample(self.current_index)

    def add_dataset(self):
        """Add another dataset to merge with the current one."""
        # Get recent annotation file and image folder
        recent_annotation_file = self.recent_paths.get("annotation_file", "")
        recent_image_folder = self.recent_paths.get("image_folder", "")

        # File dialog to select additional annotation file
        annotation_file = filedialog.askopenfilename(
            title="Select Additional COCO Annotation File",
            filetypes=[("JSON Files", "*.json")],
            initialdir=(
                os.path.dirname(recent_annotation_file)
                if recent_annotation_file
                else ""
            ),
            initialfile=(
                os.path.basename(recent_annotation_file)
                if recent_annotation_file
                else ""
            ),
        )
        if not annotation_file:
            messagebox.showinfo("Info", "No annotation file selected.")
            return

        # Directory dialog to select image folder
        image_folder = filedialog.askdirectory(
            title="Select Additional COCO Image Folder",
            initialdir=recent_image_folder if recent_image_folder else "",
        )
        if not image_folder:
            messagebox.showinfo("Info", "No image folder selected.")
            return

        # Load additional COCO dataset
        try:
            new_coco = COCO(annotation_file)

            # Show category comparison popup
            self.compare_categories(new_coco, image_folder)

            # Save recent paths
            self.recent_paths["annotation_file"] = annotation_file
            self.recent_paths["image_folder"] = image_folder
            self.save_recent_paths()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load additional dataset: {e}")

    def compare_categories(self, new_coco, new_image_folder):
        """Compare categories between the current and new datasets."""
        # Create popup window
        self.compare_window = ctk.CTkToplevel(self)
        self.compare_window.title("Compare Categories")
        self.compare_window.geometry("600x400")

        # Create a main frame
        main_frame = ctk.CTkFrame(self.compare_window)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Create a canvas and scrollbar for scrolling
        canvas = tk.Canvas(main_frame)
        scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        # Create a frame inside the canvas
        frame = ctk.CTkFrame(canvas)
        canvas.create_window((0, 0), window=frame, anchor="nw")

        # Update scrollregion when the frame size changes
        frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        # Get categories from both datasets
        existing_cats = self.coco.loadCats(self.coco.getCatIds())
        new_cats = new_coco.loadCats(new_coco.getCatIds())

        existing_cat_ids = set(cat["id"] for cat in existing_cats)
        new_cat_ids = set(cat["id"] for cat in new_cats)

        categories_match = existing_cat_ids == new_cat_ids

        # Display message based on category match
        self.display_category_comparison_message(frame, categories_match)

        # Display categories side by side
        self.display_categories_side_by_side(frame, existing_cats, new_cats)

        # Add merge and cancel buttons
        self.add_merge_cancel_buttons(frame, new_coco, new_image_folder)

        # Wait for the window to be closed before proceeding
        self.compare_window.grab_set()
        self.compare_window.wait_window()

    def display_category_comparison_message(self, frame, categories_match):
        """Display a message indicating whether categories match."""
        if categories_match:
            message_label = ctk.CTkLabel(
                frame,
                text="Categories match!",
                fg_color="green",
                text_color="white",
                corner_radius=5,
                padx=10,
                pady=5,
            )
        else:
            message_label = ctk.CTkLabel(
                frame,
                text="Warning: Categories do not match! Annotations may be lost.",
                fg_color="red",
                text_color="white",
                corner_radius=5,
                padx=10,
                pady=5,
            )
        message_label.grid(row=0, column=0, columnspan=2, pady=5)

    def display_categories_side_by_side(self, frame, existing_cats, new_cats):
        """Display categories from both datasets side by side."""
        # Create labels for the existing and new datasets
        existing_label = ctk.CTkLabel(frame, text="Target Dataset Categories")
        existing_label.grid(row=1, column=0, padx=5, pady=5)

        new_label = ctk.CTkLabel(frame, text="Source Dataset Categories")
        new_label.grid(row=1, column=1, padx=5, pady=5)

        # Get lists of category IDs and names
        existing_cat_list = sorted([(cat["id"], cat["name"]) for cat in existing_cats])
        new_cat_list = sorted([(cat["id"], cat["name"]) for cat in new_cats])

        # Determine the maximum number of categories to display
        max_rows = max(len(existing_cat_list), len(new_cat_list))

        # Display categories side by side
        for i in range(max_rows):
            if i < len(existing_cat_list):
                cat_id, cat_name = existing_cat_list[i]
                label = ctk.CTkLabel(frame, text=f"{cat_name} ({cat_id})")
                label.grid(row=i + 2, column=0, padx=5, pady=2, sticky="w")
            if i < len(new_cat_list):
                cat_id, cat_name = new_cat_list[i]
                label = ctk.CTkLabel(frame, text=f"{cat_name} ({cat_id})")
                label.grid(row=i + 2, column=1, padx=5, pady=2, sticky="w")

    def add_merge_cancel_buttons(self, frame, new_coco, new_image_folder):
        """Add merge and cancel buttons to the comparison window."""
        # Add a button frame at the bottom
        button_frame = ctk.CTkFrame(frame)
        button_frame.grid(
            row=1000, column=0, columnspan=2, pady=10
        )  # Adjusted row number

        # Merge button
        merge_button = ctk.CTkButton(
            button_frame,
            text="Merge",
            command=lambda: self.confirm_merge(new_coco, new_image_folder),
        )
        merge_button.pack(side="left", padx=10)

        # Cancel button
        cancel_button = ctk.CTkButton(
            button_frame, text="Cancel", command=self.compare_window.destroy
        )
        cancel_button.pack(side="left", padx=10)

    def confirm_merge(self, new_coco, new_image_folder):
        """Confirm and perform the merge of datasets."""
        # Proceed to merge datasets
        self.merge_datasets(new_coco, new_image_folder)

        # Close the compare window
        self.compare_window.destroy()

        # Update dataset information
        self.update_info_textbox()
        self.update_classes_textbox()
        self.update_image_index_label()

        # Display the current image
        self.display_sample(self.current_index)

    def merge_datasets(self, new_coco, new_image_folder):
        """Merge the new dataset into the current dataset."""
        existing_cat_ids = set(self.coco.getCatIds())

        # Filter new annotations
        new_ann_ids = new_coco.getAnnIds()
        new_annotations = new_coco.loadAnns(new_ann_ids)
        filtered_annotations = [
            ann for ann in new_annotations if ann["category_id"] in existing_cat_ids
        ]

        # Get image IDs for the filtered annotations
        image_ids_with_valid_annotations = set(
            ann["image_id"] for ann in filtered_annotations
        )

        # Load images corresponding to the filtered annotations
        new_images = new_coco.loadImgs(list(image_ids_with_valid_annotations))

        # Shift new image IDs and update image paths
        self.shift_image_ids_and_paths(new_images, new_image_folder)

        # Update annotations with new image IDs and shift annotation IDs
        self.update_annotations_with_new_ids(filtered_annotations)

        # Merge annotations and images
        self.coco.dataset["annotations"].extend(filtered_annotations)
        self.coco.dataset["images"].extend(new_images)
        self.image_ids.extend([img["id"] for img in new_images])

        # Rebuild the index
        self.coco.createIndex()

        # Update class colors and class list
        self.assign_class_colors()
        self.classes = [
            cat["name"] for cat in self.coco.loadCats(self.coco.getCatIds())
        ]

    def shift_image_ids_and_paths(self, new_images, new_image_folder):
        """Shift image IDs to avoid conflicts and update image paths."""
        existing_image_ids = self.coco.getImgIds()
        max_existing_image_id = max(existing_image_ids) if existing_image_ids else 0

        image_id_mapping = {}
        for img in new_images:
            old_id = img["id"]
            new_id = old_id + max_existing_image_id + 1
            img["id"] = new_id
            image_id_mapping[old_id] = new_id
            image_path = os.path.join(new_image_folder, img["file_name"])
            self.image_id_to_path[new_id] = image_path

    def update_annotations_with_new_ids(self, filtered_annotations):
        """Update annotations with new image IDs and shift annotation IDs."""
        existing_ann_ids = self.coco.getAnnIds()
        max_existing_ann_id = max(existing_ann_ids) if existing_ann_ids else 0

        for ann in filtered_annotations:
            ann["image_id"] += max_existing_ann_id + 1
            ann["id"] += max_existing_ann_id + 1

    def sub_or_over_sample_dataset(self):
        # Open a new window for subsampling/oversampling options
        self.sample_window = ctk.CTkToplevel(self)
        self.sample_window.title("Subsample/Oversample Dataset")
        self.sample_window.geometry("500x300")

        # Create a frame to organize the widgets
        frame = ctk.CTkFrame(self.sample_window)
        frame.pack(padx=20, pady=20, fill="both", expand=True)

        # Label for subsampling ratio
        subsample_ratio_label = ctk.CTkLabel(
            frame, text="Enter Subsampling Ratio (0.0 - 1.0):"
        )
        subsample_ratio_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        # Entry to input the subsampling ratio
        self.subsample_ratio_entry = ctk.CTkEntry(frame)
        self.subsample_ratio_entry.grid(row=0, column=1, padx=10, pady=10)

        # Subsample button
        subsample_button = ctk.CTkButton(
            frame, text="Subsample", command=self.apply_subsample
        )
        subsample_button.grid(row=1, column=0, columnspan=2, padx=10, pady=10)

        # Label for oversampling ratio
        oversample_ratio_label = ctk.CTkLabel(
            frame, text="Enter Oversampling Ratio (1, 2, 3, 4 ..):"
        )
        oversample_ratio_label.grid(row=2, column=0, padx=10, pady=10, sticky="w")

        # Entry to input the oversampling ratio
        self.oversample_ratio_entry = ctk.CTkEntry(frame)
        self.oversample_ratio_entry.grid(row=2, column=1, padx=10, pady=10)

        # Oversample button
        oversample_button = ctk.CTkButton(
            frame, text="Oversample", command=self.apply_oversample
        )
        oversample_button.grid(row=3, column=0, columnspan=2, padx=10, pady=10)

    def apply_subsample(self):
        """Apply subsampling to the dataset."""
        messagebox.showinfo("Info", "Subsampling is not yet implemented.")

    def apply_oversample(self):
        """Apply oversampling to the dataset."""
        messagebox.showinfo("Info", "Oversampling is not yet implemented.")

    def add_missing_segmentation_field(self):
        """Add missing 'segmentation' field to annotations."""
        counter = 0
        for annotation in self.coco.dataset.get("annotations", []):
            if "segmentation" not in annotation:
                annotation["segmentation"] = []
                counter += 1

        messagebox.showinfo(
            "Success",
            f"{counter} Missing 'segmentation' fields have been added with empty lists as default value.",
        )

    def add_missing_is_crowd_field(self):
        """Add missing 'iscrowd' field to annotations."""
        counter = 0
        for annotation in self.coco.dataset.get("annotations", []):
            if "iscrowd" not in annotation:
                annotation["iscrowd"] = 0
                counter += 1

        messagebox.showinfo(
            "Success",
            f"{counter} Missing 'iscrowd' fields have been added with default value 0.",
        )

        self.coco.createIndex()

    def manage_classes(self):
        """Open a window to manage class IDs."""

        # Open a new window
        self.manage_window = ctk.CTkToplevel(self)
        self.manage_window.title("Manage Class IDs")
        self.manage_window.geometry("600x1000")

        # Create a scrollable frame if necessary
        canvas = tk.Canvas(self.manage_window)
        scrollbar = tk.Scrollbar(
            self.manage_window, orient="vertical", command=canvas.yview
        )
        scrollable_frame = ctk.CTkFrame(canvas)

        scrollable_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # For each category, display current ID and name, entry for new ID, and delete checkbox
        self.class_entries = {}  # To store entries for new IDs
        self.class_delete_vars = {}  # To store variables for delete checkboxes
        row = 0
        for cat in self.coco.loadCats(self.coco.getCatIds()):
            cat_id = cat["id"]
            cat_name = cat["name"]

            # Display current ID and name
            label = ctk.CTkLabel(
                scrollable_frame,
                text=f"Class Name (ID): {cat_name} ({cat_id}) - Change ID to:",
            )
            label.grid(row=row, column=0, padx=5, pady=5, sticky="w")

            # Entry for new ID
            entry = ctk.CTkEntry(scrollable_frame)
            entry.grid(row=row, column=1, padx=5, pady=5)
            self.class_entries[cat_id] = entry

            # Checkbox for delete
            var = tk.BooleanVar()
            checkbox = ctk.CTkCheckBox(scrollable_frame, text="Delete", variable=var)
            checkbox.grid(row=row, column=2, padx=5, pady=5)
            self.class_delete_vars[cat_id] = var

            row += 1

        # Apply Changes button
        apply_button = ctk.CTkButton(
            scrollable_frame, text="Apply Changes", command=self.apply_class_changes
        )
        apply_button.grid(row=row, column=0, columnspan=3, pady=10)

    def apply_class_changes(self):
        # Collect new IDs and deletions
        new_ids = {}
        delete_category_ids = []
        existing_ids = set(self.coco.getCatIds())

        # First, collect new IDs and check for conflicts
        used_new_ids = set()
        for cat_id, entry in self.class_entries.items():
            new_id_str = entry.get()
            if new_id_str:
                try:
                    new_id = int(new_id_str)
                    if new_id in used_new_ids:
                        messagebox.showerror(
                            "Error",
                            f"Duplicate new ID {new_id} assigned to multiple categories.",
                        )
                        return
                    if new_id in existing_ids and new_id != cat_id:
                        messagebox.showerror(
                            "Error",
                            f"New ID {new_id} conflicts with existing category ID.",
                        )
                        return
                    new_ids[cat_id] = new_id
                    used_new_ids.add(new_id)
                except ValueError:
                    messagebox.showerror(
                        "Error", f"Invalid ID entered for category {cat_id}."
                    )
                    return

        # Collect categories to delete
        for cat_id, var in self.class_delete_vars.items():
            if var.get():
                delete_category_ids.append(cat_id)

        # Confirm deletion
        if delete_category_ids:
            result = messagebox.askyesno(
                "Confirm Deletion",
                f"Are you sure you want to delete categories {delete_category_ids}? This will remove all associated annotations.",
            )
            if not result:
                return

        # Apply changes
        # Update category IDs
        for old_id, new_id in new_ids.items():
            if old_id != new_id:
                # Update category ID in categories
                for cat in self.coco.dataset["categories"]:
                    if cat["id"] == old_id:
                        cat["id"] = new_id
                        break
                # Update category ID in annotations
                for ann in self.coco.dataset["annotations"]:
                    if ann["category_id"] == old_id:
                        ann["category_id"] = new_id
                # Update class colors
                if old_id in self.class_colors:
                    self.class_colors[new_id] = self.class_colors.pop(old_id)
                existing_ids.discard(old_id)
                existing_ids.add(new_id)

        # Delete categories and associated annotations
        if delete_category_ids:
            # Remove categories
            self.coco.dataset["categories"] = [
                cat
                for cat in self.coco.dataset["categories"]
                if cat["id"] not in delete_category_ids
            ]
            # Remove annotations
            self.coco.dataset["annotations"] = [
                ann
                for ann in self.coco.dataset["annotations"]
                if ann["category_id"] not in delete_category_ids
            ]
            # Remove class colors
            for del_id in delete_category_ids:
                if del_id in self.class_colors:
                    del self.class_colors[del_id]
            existing_ids = existing_ids.difference(set(delete_category_ids))

        # Rebuild the index
        self.coco.createIndex()

        self.assign_class_colors()

        self.update_classes_textbox()

        self.display_sample(self.current_index)

        self.manage_window.destroy()

        self.update_info_textbox()

    def export_modified_annotations(self):
        """Export the modified annotations to a JSON file."""
        default_filename = (
            os.path.splitext(self.annotation_file)[0] + "_modified.json"
            if self.annotation_file
            else "annotations_modified.json"
        )

        output_file = filedialog.asksaveasfilename(
            title="Save Modified Annotations File",
            defaultextension=".json",
            initialfile=os.path.basename(default_filename),
            filetypes=[("JSON Files", "*.json")],
        )
        if not output_file:
            messagebox.showinfo("Info", "No output file selected.")
            return

        try:
            with open(output_file, "w") as f:
                json.dump(self.coco.dataset, f)
            messagebox.showinfo("Success", f"Annotations saved to {output_file}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save annotations: {e}")

    def export_dataset(self):
        """Export the dataset including images to a specified directory."""
        output_dir = filedialog.askdirectory(title="Select Output Directory")
        if not output_dir:
            messagebox.showinfo("Info", "No output directory selected.")
            return

        # Create directories
        annotations_dir = os.path.join(output_dir, "annotations")
        images_dir = os.path.join(output_dir, "images")
        os.makedirs(annotations_dir, exist_ok=True)
        os.makedirs(images_dir, exist_ok=True)

        # Save annotations
        annotations_file = os.path.join(annotations_dir, "instances.json")
        try:
            with open(annotations_file, "w") as f:
                json.dump(self.coco.dataset, f)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save annotations: {e}")
            return

        # Copy images
        try:
            for img_id in self.image_ids:
                image_path = self.image_id_to_path[img_id]
                img_filename = os.path.basename(image_path)
                dest_path = os.path.join(images_dir, img_filename)
                if not os.path.exists(dest_path):
                    shutil.copy(image_path, dest_path)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to copy images: {e}")
            return

        messagebox.showinfo("Success", f"Dataset exported to {output_dir}")


if __name__ == "__main__":
    app = CocoDatasetGUI()
    app.mainloop()
