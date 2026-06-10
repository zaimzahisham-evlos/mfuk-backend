import uuid

def build_repository_image_key(recipe_version_code: str, filename: str) -> str:
    ext = ""
    if "." in filename:
        ext = filename.rsplit(".", 1)[-1].lower()
    suffix = f".{ext}" if ext else ""
    return f"repository-images/{recipe_version_code}/{uuid.uuid4()}{suffix}"