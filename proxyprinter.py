import os
import requests
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import tkinter as tk
from tkinter import filedialog, messagebox
from io import BytesIO
from PIL import Image
import concurrent.futures  # For async image downloading
import tempfile  # For creating temporary files

# Function to fetch card image URL using Scryfall API
def get_card_image(card_name):
    url = f"https://api.scryfall.com/cards/named?exact={card_name}"
    response = requests.get(url)
    if response.status_code == 200:
        card_data = response.json()
        if 'image_uris' in card_data and 'normal' in card_data['image_uris']:
            return card_data['image_uris']['normal']
    return None

# Function to download an image and return as BytesIO object
def download_image(image_url):
    response = requests.get(image_url)
    if response.status_code == 200:
        return BytesIO(response.content)  # Return image content as a BytesIO object
    return None

# Function to create a PDF with images in a 3x3 layout
def create_pdf(card_images, output_pdf_path):
    c = canvas.Canvas(output_pdf_path, pagesize=letter)
    width, height = letter

    # Card dimensions in points
    img_width = 180  # 2.5 inches
    img_height = 252  # 3.5 inches
    x_offset = (width - img_width * 3 - 20) / 2  # Centering horizontally
    y_offset = height - 270  # Start closer to the top

    for i, img_data in enumerate(card_images):
        # Create a temporary file to save the image
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            temp_filename = temp_file.name
            img = Image.open(img_data)
            img.save(temp_filename)  # Save image to temp file
            
            # Draw the image from the temporary file path
            c.drawImage(temp_filename, x_offset + (i % 3) * (img_width + 10), y_offset, width=img_width, height=img_height)

        # Move to the next column
        if (i + 1) % 3 == 0:  # Every three images, move down for the next row
            y_offset -= img_height  # Adjust the vertical offset for the next row

            if y_offset < img_height - 270:  # Check if there's enough space for the next row
                c.showPage()  # Start a new page
                y_offset = height - 270  # Reset y_offset for new page

    # Save the PDF after all images have been processed
    c.save()

# Main function to execute the program
def main(card_file, output_folder):
    card_images = []
    unique_cards = {}  # Dictionary to avoid duplicate downloads
    future_to_card = {}  # Mapping of future to card names

    with open(card_file, 'r') as f:
        lines = f.readlines()

    # Download all card images asynchronously
    with concurrent.futures.ThreadPoolExecutor() as executor:
        for line in lines:
            parts = line.strip().split(' ', 1)
            if len(parts) == 2:
                count, card_name = parts
                count = int(count)
                print(f"Fetching image for: {card_name} (x{count})")

                if card_name not in unique_cards:
                    # Submit the task to download the image
                    future = executor.submit(get_card_image, card_name)
                    future_to_card[future] = card_name

        # After submitting all download tasks, collect results
        for future in concurrent.futures.as_completed(future_to_card):
            card_name = future_to_card[future]
            image_url = future.result()
            
            if image_url:
                if card_name not in unique_cards:
                    img_data = download_image(image_url)
                    if img_data:
                        unique_cards[card_name] = img_data  # Store the downloaded image data
                    else:
                        print(f"Failed to download image for {card_name}")
                # Add the image data multiple times based on the count
                card_images.extend([unique_cards[card_name]] * count)
            else:
                print(f"Card not found: {card_name}")

    # Create the PDF if images were downloaded
    if card_images:
        output_pdf_path = os.path.join(output_folder, "mtg_cards.pdf")
        create_pdf(card_images, output_pdf_path)
        print(f"PDF created: {output_pdf_path}")
        messagebox.showinfo("Success", f"PDF created: {output_pdf_path}")
    else:
        messagebox.showwarning("No Images", "No images to create PDF.")

# GUI Setup
def browse_file():
    filename = filedialog.askopenfilename(title="Select Card File", filetypes=[("Text Files", "*.txt")])
    if filename:
        card_file_entry.delete(0, tk.END)
        card_file_entry.insert(0, filename)

def browse_folder():
    foldername = filedialog.askdirectory(title="Select Output Folder", initialdir=os.path.join(os.path.expanduser("~"), "Downloads"))
    if foldername:
        output_folder_entry.delete(0, tk.END)
        output_folder_entry.insert(0, foldername)

def run_program():
    card_file = card_file_entry.get()
    output_folder = output_folder_entry.get()
    if not output_folder:  # If no output folder is provided, use Downloads
        output_folder = os.path.join(os.path.expanduser("~"), "Downloads")
        output_folder_entry.insert(0, output_folder)
    if card_file:
        main(card_file, output_folder)
    else:
        messagebox.showwarning("Input Error", "Please provide the card file.")

# Create the main window
root = tk.Tk()
root.title("MTG Card Proxy Generator")

# Set default output folder to Downloads
default_output_folder = os.path.join(os.path.expanduser("~"), "Downloads")
output_folder_entry = tk.Entry(root, width=50)
output_folder_entry.insert(0, default_output_folder)

# Create UI components
tk.Label(root, text="Card File:").grid(row=0, column=0, padx=10, pady=10)
card_file_entry = tk.Entry(root, width=50)
card_file_entry.grid(row=0, column=1, padx=10, pady=10)
tk.Button(root, text="Browse", command=browse_file).grid(row=0, column=2, padx=10, pady=10)

tk.Label(root, text="Output Folder:").grid(row=1, column=0, padx=10, pady=10)
output_folder_entry.grid(row=1, column=1, padx=10, pady=10)
tk.Button(root, text="Browse", command=browse_folder).grid(row=1, column=2, padx=10, pady=10)

tk.Button(root, text="Generate PDF", command=run_program).grid(row=2, column=1, pady=20)

# Start the GUI main loop
root.mainloop()
