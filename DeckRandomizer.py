from io import BytesIO
import json
from typing import Dict, Any
import random
import re
from PIL import Image
import requests
from os import path
from imgur_python import Imgur

def extract_json(filename:str) -> Dict[str, Any]:
    data: Dict[str, Any] = {}
    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)
    card_metadata: list[Any] = data["ObjectStates"][0]["ContainedObjects"]

    print(f"first_card: {card_metadata[0]}, image_data: {card_metadata[0]["CustomDeck"]}")
    return card_metadata

class Card:
    def __init__(self, card: Dict[str, Any]):
        self.card = card
        ones_count = 0
        if "LuaScript" in card:
            match = re.search(r'elements="([01]{8})"', card["LuaScript"])
            if match:
                ones_count = match.group(1).count("1")
            # print(f'Number of 1\'s in elements: {ones_count}')

        element_names = ["sun", "moon", "fire", "air", "water", "earth", "plant", "animal"]
        chosen = random.sample(element_names, ones_count)
        elements_kwargs = {name: (name in chosen) for name in element_names}
        self.elements = Elements(**elements_kwargs)
        self.setup_thresholds()
        self.modify_card_metadata()

    def setup_thresholds(self):
        if self.card['LuaScriptState'] == "":
            print(f"No threshold for the card {self.card['Nickname']}.")
            return
        # Decode the JSON from the LuaScriptState string, if it exists
        if "LuaScriptState" in self.card:
            try:
                state_json = json.loads(self.card["LuaScriptState"])
            except Exception as e:
                print(f"Failed to decode LuaScriptState: {e}")
        self.thresholds_json = state_json['thresholds'][0]      
        # Convert the string (e.g., "00000023") to the Elements class
        threshold_str = self.thresholds_json['elements']
        # Get the number of non-zero numbers and put their values in an array
        non_zero_values = [c for i, c in enumerate(threshold_str) if c != '0']

        nonzero_element_names = [name for name, v in vars(self.elements).items() if v != 0]
        random.shuffle(nonzero_element_names)
        self.threshold = Elements()
        for val in non_zero_values:
            if nonzero_element_names:
                element = nonzero_element_names.pop()
                setattr(self.threshold, element, int(val))
            else:
                break
        self.thresholds_json['elements'] = self.threshold.encode_elements()

    def modify_card_metadata(self):
        encoded_elements = self.elements.encode_elements()
        # Replace any elements="XXXXXXXX" (where X is 0 or 1, 8 digits) with the new encoded_elements value in card["LuaScript"]
        if "LuaScript" in self.card:
            self.card["LuaScript"] = re.sub(r'elements="\d{8}"', f'elements="{encoded_elements}"', self.card["LuaScript"])
        if hasattr(self, 'thresholds_json') and self.thresholds_json:
            self.card["LuaScriptState"] = json.dumps(self.thresholds_json)

    def add_image_link(self, image_link: str) -> None:
        # Add the image link to the card's CustomDeck
        if "CustomDeck" not in self.card:
            self.card["CustomDeck"] = {}
        first_key = next(iter(self.card["CustomDeck"]), "0")
        self.card["CustomDeck"][first_key]["FaceURL"] = image_link

class Elements:
    def __init__(self, sun: int = 0, moon: int = 0, fire: int = 0, air: int = 0,
                 water: int = 0, earth: int = 0, plant: int = 0, animal: int = 0):
        self.sun = sun
        self.moon = moon
        self.fire = fire
        self.air = air
        self.water = water
        self.earth = earth
        self.plant = plant
        self.animal = animal

    def __str__(self):
        return self.encode_elements()

    def encode_elements(self) -> str:
        # Sun, Moon, Fire, Air, Water, Earth, Plant, Animal
        return f"{int(self.sun)}{int(self.moon)}{int(self.fire)}{int(self.air)}" \
               f"{int(self.water)}{int(self.earth)}{int(self.plant)}{int(self.animal)}"



def gen_card_image(card: Card) -> None:
    first_key = next(iter(card.card["CustomDeck"]))
    response = requests.get(card.card["CustomDeck"][first_key]["FaceURL"])
    image = Image.open(BytesIO(response.content))
    # Overlay elements.png image onto the card image
    elements_img = Image.open("Assets/elements.png").convert("RGBA")
    image = image.convert("RGBA")
    # Define the position (top-left corner) where the elements image should be pasted
    # For example, bottom right corner with 10px margin
    pos_x = 50
    pos_y = 200
    # Overlay the elements image onto the card image at the specified position
    image.alpha_composite(elements_img, dest=(pos_x, pos_y))

    # Now, we can add the elements to the card image
    element_images = {
        "sun": "Assets/Esun.png",
        "moon": "Assets/Emoon.png",
        "fire": "Assets/Efire.png",
        "air": "Assets/Eair.png",
        "water": "Assets/Ewater.png",
        "earth": "Assets/Eearth.png",
        "plant": "Assets/Eplant.png",
        "animal": "Assets/Eanimal.png"
    }
    # Define offsets and spacing for each element
    element_offsets = {
        "sun": (0, 98 * 0),
        "moon": (0, 98 * 1),
        "fire": (0, 98 * 2),
        "air": (0, 98 * 3),
        "water": (0, 98 * 4),
        "earth": (0, 98 * 5),
        "plant": (0, 98 * 6),
        "animal": (0, 98 * 7)
    }

    # Draw each element if present
    for element, img_path in element_images.items():
        if getattr(card.elements, element):
            offset_x, offset_y = element_offsets[element]
            element_img = Image.open(img_path).convert("RGBA")
            image.alpha_composite(element_img, dest=(pos_x + offset_x, pos_y + offset_y))

    # Draw the threshold elements
    if hasattr(card, 'threshold') and card.threshold:
        start_x, start_y = 360 - (360 * card.thresholds_json['position']['x']) + 60, 430 + 420 * card.thresholds_json['position']['z']
        cur_x, cur_y = int(start_x), int(start_y)
        thresh_element_images = {
            "sun": "Assets/thresh_Esun.png",
            "moon": "Assets/thresh_Emoon.png",
            "fire": "Assets/thresh_Efire.png",
            "air": "Assets/thresh_Eair.png",
            "water": "Assets/thresh_Ewater.png",
            "earth": "Assets/thresh_Eearth.png",
            "plant": "Assets/thresh_Eplant.png",
            "animal": "Assets/thresh_Eanimal.png",
            "2": "Assets/2.png",
            "3": "Assets/3.png",
            "4": "Assets/4.png",
        }
        # Draw threshold elements for each element type
        for element in ["sun", "moon", "fire", "air", "water", "earth", "plant", "animal"]:
            value = getattr(card.threshold, element, 0)
            # Draw the number image if value > 1
            if value > 1:
                num_img = Image.open(thresh_element_images[str(value)]).convert("RGBA")
                image.alpha_composite(num_img, dest=(cur_x, cur_y))
                cur_x += num_img.width
                # Draw the element image
                element_img = Image.open(thresh_element_images[element]).convert("RGBA")
                image.alpha_composite(element_img, dest=(cur_x, cur_y))
                cur_x += element_img.width


    # Optionally save or display the result
    image.save(f"out/{card.card.get('Nickname', 'card')} Randomized.png")
    return

def run(file_name:str = "Minor Powers.json"):
    card_metadata = extract_json(file_name)
    for card_json in card_metadata:
        if isinstance(card_json, dict) and "LuaScript" in card_json:
            print(f"Processing card: {card_json['Nickname']}")
            card = Card(card_json)
            gen_card_image(card)
            card.add_image_link(f"https://raw.githubusercontent.com/Appl3wow/Si-Deck-Randomizer/refs/heads/main/V0/{card_json['Nickname']} Randomized.png")
            card_json = card.card
        else:
            print("Skipping non-card object or missing LuaScript.")

    print("All cards processed.")
    print(card_metadata[0])  # Print the first card metadata for verification
    # Overwrite the previous file if it exists by opening in write mode ('w')
    with open(f"out/{file_name} Randomized.json", "w", encoding="utf-8") as f:
        json.dump(card_metadata, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    run("Major Powers.json")
    run("Minor Powers.json")
