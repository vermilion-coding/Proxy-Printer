import os
import requests
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import tkinter as tk
from tkinter import filedialog, messagebox
from io import BytesIO
from PIL import Image

# Function to fetch card image URL using Scryfall API
def get_card_image(card_name):
    url = f"https://api.scryfall.com/cards/named?exact={card_name}"
    response = requests.get(url)
    
    if response.status_code == 200:
        card_data = response.json()
        if 'image_uris' in card_data and 'normal' in card_data['image_uris']:
            return card_data['image_uris']['normal']
    return None

# Function to download an image and return as bytes
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
        # Create an in-memory image and draw it
        img = Image.open(img_data)
        temp_filename = f"temp_{i}.png"  # Unique temp file name for each image
        img.save(temp_filename)  # Save temporarily to draw
        c.drawImage(temp_filename, x_offset + (i % 3) * (img_width + 10), y_offset, width=img_width, height=img_height)

        # Move to the next column
        if (i + 1) % 3 == 0:  # Every three images, move down for the next row
            y_offset -= img_height  # Adjust the vertical offset for the next row

            if y_offset < img_height - 270:  # Check if there's enough space for the next row
                c.showPage()  # Start a new page
                y_offset = height - 270  # Reset y_offset for new page

    # Save the PDF after all images have been processed
    c.save()

    # Clean up temporary files
    for i in range(len(card_images)):
        os.remove(f"temp_{i}.png")  # Remove each temporary file

# Main function to execute the program
def main(card_file, output_folder):
    card_images = []
    unique_cards = {}  # Dictionary to avoid duplicate downloads
    
    with open(card_file, 'r') as f:
        lines = f.readlines()
    
    for line in lines:
        parts = line.strip().split(' ', 1)
        if len(parts) == 2:
            count, card_name = parts
            count = int(count)
            print(f"Fetching image for: {card_name} (x{count})")
            image_url = get_card_image(card_name)
            
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
    foldername = filedialog.askdirectory(title="Select Output Folder")
    if foldername:
        output_folder_entry.delete(0, tk.END)
        output_folder_entry.insert(0, foldername)

def run_program():
    card_file = card_file_entry.get()
    output_folder = output_folder_entry.get()
    if card_file and output_folder:
        main(card_file, output_folder)
    else:
        messagebox.showwarning("Input Error", "Please provide both the card file and output folder.")

# Create the main window
root = tk.Tk()
root.title("MTG Card Proxy Generator")

# Create UI components
tk.Label(root, text="Card File:").grid(row=0, column=0, padx=10, pady=10)
card_file_entry = tk.Entry(root, width=50)
card_file_entry.grid(row=0, column=1, padx=10, pady=10)
tk.Button(root, text="Browse", command=browse_file).grid(row=0, column=2, padx=10, pady=10)

tk.Label(root, text="Output Folder:").grid(row=1, column=0, padx=10, pady=10)
output_folder_entry = tk.Entry(root, width=50)
output_folder_entry.grid(row=1, column=1, padx=10, pady=10)
tk.Button(root, text="Browse", command=browse_folder).grid(row=1, column=2, padx=10, pady=10)

tk.Button(root, text="Generate PDF", command=run_program).grid(row=2, column=1, pady=20)

# Start the GUI main loop
root.mainloop()
