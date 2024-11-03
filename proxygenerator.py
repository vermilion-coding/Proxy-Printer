import os
import requests
from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import tkinter as tk
from tkinter import filedialog, messagebox

# Function to fetch card image URL using Scryfall API
def get_card_image(card_name):
    url = f"https://api.scryfall.com/cards/named?exact={card_name}"
    response = requests.get(url)
    
    if response.status_code == 200:
        card_data = response.json()
        if 'image_uris' in card_data and 'normal' in card_data['image_uris']:
            return card_data['image_uris']['normal']
    return None

# Function to download an image and save it locally
def download_image(image_url, save_path):
    response = requests.get(image_url)
    if response.status_code == 200:
        with open(save_path, 'wb') as f:
            f.write(response.content)
        return True
    return False

# Function to create a PDF with images in a 3x3 layout
def create_pdf(card_images, output_pdf_path):
    c = canvas.Canvas(output_pdf_path, pagesize=letter)
    width, height = letter
    
    x_offset = 50
    y_offset = height - 50
    img_width = (width - 100) / 3
    img_height = (height - 100) / 3
    
    for i, img_path in enumerate(card_images):
        if i % 3 == 0 and i > 0:
            y_offset -= img_height + 10
            x_offset = 50
            
        if y_offset < 50:  # Move to the next page if the space is not enough
            c.showPage()
            y_offset = height - 50
        
        c.drawImage(img_path, x_offset, y_offset, width=img_width, height=img_height)
        x_offset += img_width + 10

    c.save()

# Main function to execute the program
def main(card_file, output_folder):
    card_images = []
    
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
                for _ in range(count):
                    img_path = os.path.join(output_folder, f"{card_name}.png")
                    if download_image(image_url, img_path):
                        card_images.append(img_path)
                    else:
                        print(f"Failed to download image for {card_name}")
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
