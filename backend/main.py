from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import openai
import os

app = FastAPI()

# Initialize OpenAI API client
openai.api_key = 'API KEY'

# Store items
store_items = [
    {"name": "dosa", "description": "A thin pancake originating from South India"},
    {"name": "upma", "description": "A breakfast dish made from semolina"},
    {"name": "idli", "description": "A type of savoury rice cake"},
    {"name": "vada", "description": "A savoury fried snack"},
    {"name": "lemon rice", "description": "Rice with lemon flavor"},
    {"name": "curd rice", "description": "Rice mixed with curd"}
]



app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Path to the build directory of your React project
build_directory = os.path.join(os.path.dirname(__file__), '..', 'my-app', 'build')
# Serve the static files

app.mount("/static", StaticFiles(directory=os.path.join(build_directory, 'static')), name="static")
app.mount("/", StaticFiles(directory=build_directory, html=True), name="build")

# Serve the root HTML file
@app.get("/", response_class=HTMLResponse)
async def get_root():
    with open(os.path.join(build_directory, 'index.html')) as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)

# Function to search store items
def search_store_items(query):
    for item in store_items:
        if query.lower() in item['name'].lower():
            return item
    return None

# Function to ask for feedback
def ask_for_feedback():
    return "Thank you for your order. We would love to hear your feedback on your experience. Please let us know if there is anything we can improve or if everything was perfect."

# Process and analyze the feedback
def process_feedback(feedback):
    with open('feedback_log.txt', 'a') as f:
        f.write(feedback + "\n")

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    file_location = f"temp/{file.filename}"

    # Ensure the temp directory exists
    os.makedirs(os.path.dirname(file_location), exist_ok=True)

    # Save the uploaded file
    with open(file_location, "wb+") as file_object:
        file_object.write(file.file.read())

    # Transcribe the audio file using Whisper API
    print("Transcribing...")
    audio_file_path = os.path.abspath(file_location)
    with open(audio_file_path, "rb") as audio_file:
        response = openai.Audio.transcribe("whisper-1", audio_file)
    transcribed_text = response['text']
    print("Transcribed Text:", transcribed_text)

    # Search for the item
    searched_item = search_store_items(transcribed_text)

    # Generate the prompt based on the search result
    if searched_item:
        item_name = searched_item['name']
        item_description = searched_item['description']
        order_prompt = f"The customer said: '{transcribed_text}'. I found the item: {item_name} - {item_description}. Would you like to have any specifications with that? If yes, would you like to send it as a recording itself, or would you just directly like to tell the specifications?"
    else:
        order_prompt = f"The customer said: '{transcribed_text}'. I couldn't find the exact item. Can you please repeat or specify your order? The available items are: {', '.join([item['name'] for item in store_items])}."

    # Use the OpenAI API to generate a response
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": """You are a helpful assistant at a South Indian store. After the order is placed, ask if there is anything else they would like to say about the order. If no, place the order, and give your own prices including GST for all items on the menu."""},
            {"role": "user", "content": order_prompt}
        ]
    )

    # Get AI response
    ai_response = response['choices'][0]['message']['content'].strip()
    print(ai_response)

    # Generate and print feedback request
    feedback_prompt = ask_for_feedback()
    feedback_response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant at a South Indian store."},
            {"role": "user", "content": feedback_prompt}
        ]
    )
    feedback_request = feedback_response['choices'][0]['message']['content'].strip()
    print(feedback_request)

    return {"transcription": transcribed_text, "response": ai_response, "feedback": feedback_request}

# Running the server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
