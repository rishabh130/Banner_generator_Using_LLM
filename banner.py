from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import uuid
import requests  # Required to download from URL

from together import Together

# Load env
load_dotenv()
API_KEY = os.getenv("TOGETHER_API_KEY")

client = Together(api_key=API_KEY)
app = FastAPI()

IMAGE_DIR = "images"
os.makedirs(IMAGE_DIR, exist_ok=True)

class PromptInput(BaseModel):
   prompt: str

@app.post("/generate-image")
def generate_image(input: PromptInput):
   try:
       full_prompt = (
           input.prompt +
           " Also, strictly avoid text or decorative elements in the banner image to maintain professionalism."
       )

       response = client.images.generate(
           prompt=full_prompt,
           model="black-forest-labs/FLUX.1-schnell-Free",
           steps=1,  #  required max is 4, safe with 1
           n=1
       )

       print("Raw Together API response:", response)

       # Get image URL instead of b64_json
       image_url = response.data[0].url
       if not image_url:
           raise HTTPException(status_code=500, detail="No image URL returned by API.")

       image_id = str(uuid.uuid4())
       file_path = os.path.join(IMAGE_DIR, f"{image_id}.png")

       # Download image from URL
       img_data = requests.get(image_url).content
       with open(file_path, "wb") as f:
           f.write(img_data)

       return {"message": "Image created", "image_id": image_id}

   except Exception as e:
       print("Exception occurred:", str(e))
       raise HTTPException(status_code=500, detail=f"Failed to generate image: {str(e)}")

@app.get("/download-image/{image_id}")
def download_image(image_id: str):
   file_path = os.path.join(IMAGE_DIR, f"{image_id}.png")
   if not os.path.exists(file_path):
       raise HTTPException(status_code=404, detail="Image not found")
   return FileResponse(path=file_path, media_type="image/png", filename=f"{image_id}.png")



