import tkinter as tk
import customtkinter as ctk
from PIL import Image, ImageTk, ImageDraw, ImageFont
from pycocotools.coco import COCO
import os
import random
from tkinter import filedialog, messagebox, simpledialog
import json  # Added to handle JSON operations

# Initialize customtkinter
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class CocoDatasetGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("COCO Dataset GUI Tool")
        self.geometry("1000x700")

        # Initialize dataset variables
        self.coco = None
        self.image_folder = None
        self.image_ids = []
        self.current_index = 0
        self.annotation_file = None  # Added to store the original annotation file path

        self.dataset_info = f"<INFO PLACEHOLDER>"

        # Class colors
        self.class_colors = {}
        self.classes = []

        # Image ID to file path mapping
        self.image_id_to_path = {}

        # Setup GUI elements
        self.setup_gui()

        # Prompt user to select files
        self.select_files()

    def setup_gui(self):
        # Main frame
        self.frame = ctk.CTkFrame(master=self)
        self.frame.pack(pady=10, padx=10, fill="both", expand=True)

        # Top frame for navigation and image info
        self.top_frame = ctk.CTkFrame(master=self.frame)
        self.top_frame.pack(pady=5, padx=5, fill="x")

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

        # Image display label
        self.image_label = ctk.CTkLabel(master=self.frame, text="")
        self.image_label.pack(pady=10)

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

        # Control buttons frame
        self.control_frame = ctk.CTkFrame(master=self.frame)
        self.control_frame.pack(pady=10, padx=10, fill="x")

        # Button to add another dataset
        self.add_dataset_button = ctk.CTkButton(
            master=self.control_frame,
            text="Add Another Dataset",
            command=self.add_dataset,
        )
        self.add_dataset_button.pack(side="left", padx=10)

        # Button to manage classes (change IDs or delete)
        self.manage_classes_button = ctk.CTkButton(
            master=self.control_frame,
            text="Manage Classes",
            command=self.manage_classes,
        )
        self.manage_classes_button.pack(side="left", padx=10)

        # Button to export the modified dataset
        self.export_button = ctk.CTkButton(
            master=self.control_frame,
            text="Export Dataset",
            command=self.export_dataset,
        )
        self.export_button.pack(side="left", padx=10)

    def select_files(self):
        # File dialog to select annotation file
        annotation_file = filedialog.askopenfilename(
            title="Select COCO Annotation File", filetypes=[("JSON Files", "*.json")]
        )
        if not annotation_file:
            messagebox.showerror("Error", "No annotation file selected.")
            self.quit()
            return

        self.annotation_file = annotation_file  # Store the annotation file path

        # Directory dialog to select image folder
        image_folder = filedialog.askdirectory(title="Select COCO Image Folder")
        if not image_folder:
            messagebox.showerror("Error", "No image folder selected.")
            self.quit()
            return

        # Load COCO dataset
        try:
            self.coco = COCO(annotation_file)
            self.image_folder = image_folder
            self.image_ids = self.coco.getImgIds()
            self.current_index = 0

            # Map image IDs to file paths
            for img_info in self.coco.loadImgs(self.image_ids):
                image_path = os.path.join(self.image_folder, img_info["file_name"])
                self.image_id_to_path[img_info["id"]] = image_path

            # Get list of classes
            cats = self.coco.loadCats(self.coco.getCatIds())
            self.classes = [cat["name"] for cat in cats]
            self.assign_class_colors()

            # Update dataset information
            self.update_info_textbox()
            self.update_classes_textbox()
            self.update_image_index_label()

            # Display the first image and annotations
            self.display_sample(self.current_index)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load dataset: {e}")
            self.quit()

    def assign_class_colors(self):
        random.seed(42)  # For reproducibility
        for cat_id in self.coco.getCatIds():
            self.class_colors[cat_id] = (
                random.randint(0, 255),
                random.randint(0, 255),
                random.randint(0, 255),
            )

    def update_info_textbox(self):
        self.info_textbox.configure(state="normal")
        self.info_textbox.delete("1.0", tk.END)
        self.info_textbox.insert("1.0", self.dataset_info)
        self.info_textbox.configure(state="disabled")

    def update_classes_textbox(self):
        self.classes_textbox.configure(state="normal")
        self.classes_textbox.delete("1.0", tk.END)
        self.classes_textbox.insert("1.0", "Classes:\n")
        for cat_id in sorted(self.coco.getCatIds()):
            cat = self.coco.loadCats(cat_id)[0]
            self.classes_textbox.insert(tk.END, f"{cat_id}: {cat['name']}\n")
        self.classes_textbox.configure(state="disabled")

    def update_image_index_label(self):
        self.image_index_label.configure(
            text=f"Image {self.current_index + 1}/{len(self.image_ids)}"
        )

    def display_sample(self, index):
        if not self.image_ids:
            return

        # Get image info
        img_info = self.coco.loadImgs(self.image_ids[index])[0]
        image_id = img_info["id"]
        image_path = self.image_id_to_path.get(image_id)

        # Open image
        try:
            image = Image.open(image_path).convert("RGB")
        except FileNotFoundError:
            messagebox.showerror("Error", f"Image file not found: {image_path}")
            return

        # Draw annotations
        ann_ids = self.coco.getAnnIds(imgIds=img_info["id"])
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

        # Resize image to fit the GUI window
        image.thumbnail((800, 600))
        self.photo = ImageTk.PhotoImage(image)

        # Update image label
        self.image_label.configure(image=self.photo)
        self.image_label.image = self.photo

        # Update image index label
        self.update_image_index_label()

    def next_sample(self):
        if not self.image_ids:
            return
        # Increment index and loop back if necessary
        self.current_index = (self.current_index + 1) % len(self.image_ids)
        self.display_sample(self.current_index)

    def prev_sample(self):
        if not self.image_ids:
            return
        # Decrement index and loop back if necessary
        self.current_index = (self.current_index - 1) % len(self.image_ids)
        self.display_sample(self.current_index)

    def add_dataset(self):
        # File dialog to select additional annotation file
        annotation_file = filedialog.askopenfilename(
            title="Select Additional COCO Annotation File",
            filetypes=[("JSON Files", "*.json")],
        )
        if not annotation_file:
            messagebox.showinfo("Info", "No annotation file selected.")
            return

        # Directory dialog to select image folder
        image_folder = filedialog.askdirectory(
            title="Select Additional COCO Image Folder"
        )
        if not image_folder:
            messagebox.showinfo("Info", "No image folder selected.")
            return

        # Load additional COCO dataset
        try:
            new_coco = COCO(annotation_file)
            new_image_folder = image_folder
            new_image_ids = new_coco.getImgIds()

            # Check if category IDs match
            if self.categories_match(new_coco):
                # Merge datasets
                self.merge_datasets(new_coco, new_image_folder)
                # Update dataset information
                self.update_info_textbox()
                self.update_classes_textbox()
                self.update_image_index_label()

                # Display the current image
                self.display_sample(self.current_index)
            else:
                messagebox.showwarning(
                    "Warning", "Category IDs do not match. Cannot merge datasets."
                )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load additional dataset: {e}")

    def categories_match(self, new_coco):
        # Get existing category IDs
        existing_cat_ids = set(
            [cat["id"] for cat in self.coco.loadCats(self.coco.getCatIds())]
        )
        # Get new category IDs
        new_cat_ids = set(
            [cat["id"] for cat in new_coco.loadCats(new_coco.getCatIds())]
        )

        # Check if the category IDs match
        return existing_cat_ids == new_cat_ids

    def merge_datasets(self, new_coco, new_image_folder):
        # Merge images
        new_images = new_coco.dataset["images"]

        # Get the max image ID in existing dataset
        existing_image_ids = [img["id"] for img in self.coco.dataset["images"]]
        if existing_image_ids:
            max_existing_image_id = max(existing_image_ids)
        else:
            max_existing_image_id = 0

        # Shift new image IDs
        image_id_mapping = {}
        for img in new_images:
            old_id = img["id"]
            new_id = old_id + max_existing_image_id + 1
            img["id"] = new_id
            image_id_mapping[old_id] = new_id
            # Update image path
            image_path = os.path.join(new_image_folder, img["file_name"])
            self.image_id_to_path[new_id] = image_path

        # Update annotations in new_coco with new image IDs
        for ann in new_coco.dataset["annotations"]:
            ann["image_id"] = image_id_mapping[ann["image_id"]]

        self.coco.dataset["images"].extend(new_images)
        self.image_ids.extend([img["id"] for img in new_images])

        # Merge annotations
        new_annotations = new_coco.dataset["annotations"]

        # Get the max annotation ID in existing dataset
        existing_ann_ids = [ann["id"] for ann in self.coco.dataset["annotations"]]
        if existing_ann_ids:
            max_existing_ann_id = max(existing_ann_ids)
        else:
            max_existing_ann_id = 0

        # Shift new annotation IDs
        for ann in new_annotations:
            ann["id"] += max_existing_ann_id + 1

        self.coco.dataset["annotations"].extend(new_annotations)

        # Rebuild the index
        self.coco.createIndex()

        # Update class colors
        self.assign_class_colors()

        # Update class list
        self.classes = [
            cat["name"] for cat in self.coco.loadCats(self.coco.getCatIds())
        ]

    def manage_classes(self):
        # Open a new window
        self.manage_window = ctk.CTkToplevel(self)
        self.manage_window.title("Manage Classes")
        self.manage_window.geometry("400x600")

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
                scrollable_frame, text=f"ID: {cat_id}, Name: {cat_name}"
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
        delete_ids = []
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
                delete_ids.append(cat_id)

        # Confirm deletion
        if delete_ids:
            result = messagebox.askyesno(
                "Confirm Deletion",
                f"Are you sure you want to delete categories {delete_ids}? This will remove all associated annotations.",
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
        if delete_ids:
            # Remove categories
            self.coco.dataset["categories"] = [
                cat
                for cat in self.coco.dataset["categories"]
                if cat["id"] not in delete_ids
            ]
            # Remove annotations
            self.coco.dataset["annotations"] = [
                ann
                for ann in self.coco.dataset["annotations"]
                if ann["category_id"] not in delete_ids
            ]
            # Remove class colors
            for del_id in delete_ids:
                if del_id in self.class_colors:
                    del self.class_colors[del_id]
            existing_ids = existing_ids.difference(set(delete_ids))

        # Rebuild the index
        self.coco.createIndex()

        # Update class colors
        self.assign_class_colors()

        # Update class list
        self.update_classes_textbox()

        # Refresh the display
        self.display_sample(self.current_index)

        # Close the manage window
        self.manage_window.destroy()

    def export_dataset(self):
        # Default output filename
        default_filename = os.path.splitext(self.annotation_file)[0] + "_modified.json"

        # Ask user for output filename
        output_file = filedialog.asksaveasfilename(
            title="Save COCO Annotation File",
            defaultextension=".json",
            initialfile=os.path.basename(default_filename),
            filetypes=[("JSON Files", "*.json")],
        )
        if not output_file:
            messagebox.showinfo("Info", "No output file selected.")
            return

        # Save the dataset
        try:
            with open(output_file, "w") as f:
                json.dump(self.coco.dataset, f)
            messagebox.showinfo("Success", f"Dataset saved to {output_file}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save dataset: {e}")

    # Additional methods can be added here


if __name__ == "__main__":
    app = CocoDatasetGUI()
    app.mainloop()
