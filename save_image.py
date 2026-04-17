import os
from PIL import Image
import requests
from io import BytesIO

# This is a helper script to save the vegetable background image

def save_image():
    # Create the directory if it doesn't exist
    os.makedirs('static/Images', exist_ok=True)
    
    # URL of the vegetable background image
    image_url = "https://raw.githubusercontent.com/yourgithubusername/FreshMarketPlace/main/static/Images/vegetables-dark-background.jpg"
    
    try:
        # Try to download the image
        response = requests.get(image_url)
        if response.status_code == 200:
            img = Image.open(BytesIO(response.content))
        else:
            # If download fails, create a placeholder image
            img = Image.new('RGB', (1920, 1080), color='#2C2C2C')
    except:
        # If there's any error, create a placeholder image
        img = Image.new('RGB', (1920, 1080), color='#2C2C2C')
    
    # Save the image
    output_path = 'static/Images/vegetables-dark-background.jpg'
    img.save(output_path, quality=95)
    print(f"Image saved successfully at {output_path}")

if __name__ == "__main__":
    save_image() 