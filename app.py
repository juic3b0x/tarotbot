import json
import os
import random
import sqlite3
import openai
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
messages = [
    {"role": "system",
     "content": "You are a master tarot card reader, and you can give you insights into life using the ancient art of tarot."},
    {"role": "system", "content": "The response should be in the format of '[Card Name]\\n\\n[Interpretation]'."}
]

# Load the tarot_deck.json file
with open("data/tarot_deck.json", "r") as f:
    tarot_deck = json.load(f)
    deck = tarot_deck["cards"]

# Create mapping of card names to image paths
card_mapping = {}
for card in tarot_deck["cards"]:
    card_name = card.get("name")
    img_file_name = card["img"]
    card_mapping[card_name] = os.path.join("card_imgs", img_file_name)


# Define function for generating AI response
def generate_response(input):
    global messages  # Declare messages as a global variable
    global card_name  # Declare card_name as a global variable

    if input:
        messages.append({"role": "user", "content": input})
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo", messages=messages, max_tokens=1024, temperature=0.7
        )
        reply = response['choices'][0]['message']['content']  # type: ignore
        card_name = ""
        for name in card_mapping:
            if name in reply:
                card_name = name
                break
        messages.append({"role": "assistant", "content": reply})
        # Save messages to a JSON file
        with open("data/history.json", "a") as m:
            json.dump(messages, m)
            m.write("\n")

        # Save messages to a SQLite database
        conn = sqlite3.connect("data/history.db")
        c = conn.cursor()
        c.execute('''INSERT INTO messages
                     (role, user_input, assistant_response)
                     VALUES (?, ?, ?)''', (messages[-2]["role"], messages[-2]["content"], messages[-1]["content"]))
        conn.commit()
        conn.close()

        # Flush messages variable
        messages = []

        return card_name, reply


# Define Streamlit app
def app():
    global card_name
    global deck  # Declare deck as a global variable

    # Define the layout of the page
    st.set_page_config(page_title="Tarot Card Reader", page_icon="🔯", layout="wide")

    button_row = st.container()  # create container for buttons
    # Define the columns
    col1, col2, col3 = st.columns(3)

    # Define the button row
    with button_row:
        # Add button for shuffling deck in col2
        if st.button("Shuffle Deck", key="shuffle"):
            with st.spinner('Shuffling deck...'):
                # Shuffle the deck
                random.shuffle(deck)
                st.success('Deck shuffled!', icon="✅")

        # Add button for clearing results in col3
        if st.button("Clear Results", key="clear"):
            with st.spinner('Clearing results...'):
                # Clear the results
                col2.empty()
                col3.empty()
                st.success('Results cleared!', icon="✅")

    # Display the card image and interpretation
    col2.header("Your Card")
    card_image = col2.empty()  # create empty slot for card image

    col3.header("Your Reading")
    reading_text = col3.empty()  # create empty slot for reading text

    col1.header("Ascended Master Tarot")
    col1.image("./static/fortune_teller.png", use_column_width=True)
    col1.write(
        "Simply draw a card, and we'll delve into the mysteries of the universe to uncover the answers you seek. Explore the secrets of your destiny with the Ascended Master Tarot today!")
    if col1.button("Draw A Card"):
        with st.spinner('Drawing a card...'):
            # Generate AI response
            card_name, reply = generate_response(
                "Draw a random card from the deck. Please respond in the format of '[Card Name]\\n\\n[Interpretation]'.")

            # Check if card name is valid
            if card_name not in card_mapping:
                card_image.write("Invalid card name!")
            else:
                img_path = card_mapping[card_name]
                col2.subheader(card_name)
                card_image.image(img_path, use_column_width=True)
                reading_text.write(reply)
            return img_path


if __name__ == "__main__":
    app()
