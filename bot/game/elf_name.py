import random

# Lists of syllables for Christmas elf names
first_syllables = ["Jolly", "Merry", "Buddy", "Twinkle", "Sugar", "Candy", "Ginger", "Peppermint", "Sparkle", "Frosty"]
last_syllables = ["Spark", "Bell", "Cheer", "Snow", "Jingle", "Cookie", "Toes", "Claus", "Berry", "Mistletoe"]

# Function to generate a random Christmas elf name ending with "elf"
def generate_christmas_elf_name():
    first_part = random.choice(first_syllables)
    last_part = random.choice(last_syllables)
    return first_part + last_part + "_elf"
