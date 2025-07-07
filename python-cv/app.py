import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from cv_utils import extract_vector
import uvicorn

app = FastAPI()

@app.post("/process-image/")
async def process_image(file: UploadFile = File(...)):
    """
    Accepts an image file, passes it to the CV utility for processing,
    and returns the resulting feature vector.
    """
    try:
        image_bytes = await file.read()
        feature_vector = extract_vector(image_bytes)

        if not feature_vector:
            raise HTTPException(
                status_code=400, 
                detail="Could not extract a valid feature vector from the provided image."
            )

        return {"feature_vector": feature_vector}

    except Exception as e:
        # Log the exception for debugging
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail="An internal error occurred during image processing.")

@app.get("/")
def read_root():
    """Health check endpoint."""
    return {"message": "Shape Recognition Microservice is running."}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
