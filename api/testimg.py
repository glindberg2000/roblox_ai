import base64
from openai import OpenAI

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)
# Function to encode the image into base64 format
def encode_image(image_path: str) -> str:
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# Function to generate AI description using the gpt-4o-mini model
def generate_ai_description_from_image(image_path: str) -> str:
    # Encode the image into base64
    base64_image = encode_image(image_path)
    
    # Sending the image to the OpenAI API for detailed avatar description
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # Using gpt-4o-mini model
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "Please provide a detailed description of this Roblox avatar. "
                            "Include details about the avatar's clothing, accessories, colors, any unique features, "
                            "and its overall style or theme. The description will be used by NPCs in a game to "
                            "interact with the player based on their appearance."
                        ),
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        },
                    }
                ],
            }
        ]
    )

    # Debugging: print the raw response
    print(f"Raw response from OpenAI: {response}")

    # Extract and return the AI-generated description
    try:
        description = response.choices[0].message.content  # Correct attribute access
        return description
    except AttributeError as e:
        # Handle the case where the structure is different or there's an issue
        print(f"Error accessing the response content: {e}")
        return "No description available"

# Add a main section for manual testing
if __name__ == "__main__":
    image_path = "./stored_images/962483389.png"  # Path to the stored image
    print(f"Testing with image: {image_path}")
    
    try:
        description = generate_ai_description_from_image(image_path)
        print(f"AI-Generated Description: {description}")
    except Exception as e:
        print(f"Error generating description: {e}")