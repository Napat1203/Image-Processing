def process(image_bytes, user_id):
    return {
        "user_id": user_id,
        "status": "ok",
        "note": "(Demo)Image processed successfully!",
        "image_bytes": image_bytes,
    }