from PIL import Image
import requests
from io import BytesIO

eleboon_image_link = "https://steamusercontent-a.akamaihd.net/ugc/2050875404517324968/BC3C443442CD0FB1E717ACF9242EBD3A27D91AF1/"
utg_image_link = "https://steamusercontent-a.akamaihd.net/ugc/2050875404517290321/91011142B16F19FCDFB7BABC17248D7B4FB9AA3B/"

def AssetMaker():
    response = requests.get(utg_image_link)
    image = Image.open(BytesIO(response.content))
    x, z = .58, .81
    offset = 50
    element_img = Image.open("Assets/thresh_Eair.png").convert("RGBA")
    pos_x = 360 - (360 * .58) + 60 # image.width / x
    pos_y = 430 + 430 * z
    image.alpha_composite(element_img, dest=(int(pos_x), int(pos_y)))
    image.save("out/treshold_test.png")

def generate_thresholds_images():
    response = requests.get(utg_image_link)
    image = Image.open(BytesIO(response.content))
    
    crop_box = (205, 778, 655, 820)  # Example values, adjust as needed
    image = image.crop(crop_box)
    image.save("out/threshold_elements.png")

    # get elemental filled images
    response = requests.get(utg_image_link)
    image = Image.open(BytesIO(response.content))
    for i in range(8):
        # Define the box to crop: (left, upper, right, lower)
        crop_box = (228 + i*55.5, 779, 264 + i*55.5, 819)
        image_cropped = image.crop(crop_box)
        element_names = ["sun", "moon", "fire", "air", "water", "earth", "plant", "animal"]
        image_cropped.save(f"out/thresh_E{element_names[i]}.png")

def generate_elements_images():
    response = requests.get(eleboon_image_link)
    image = Image.open(BytesIO(response.content))
    # Define the box to crop: (left, upper, right, lower)
    crop_box = (50, 200, 140, 980)  # Example values, adjust as needed
    image = image.crop(crop_box)
    image.save("out/Elements.png")

    # get elemental filled images
    response = requests.get(utg_image_link)
    image = Image.open(BytesIO(response.content))
    for i in range(8):
        # Define the box to crop: (left, upper, right, lower)
        crop_box = (50, 200 + (i * 98), 140, 295 + (i * 98))
        image_cropped = image.crop(crop_box)
        element_names = ["sun", "moon", "fire", "air", "water", "earth", "plant", "animal"]
        image_cropped.save(f"out/E{element_names[i]}.png")
    

if __name__ == "__main__":
    AssetMaker()