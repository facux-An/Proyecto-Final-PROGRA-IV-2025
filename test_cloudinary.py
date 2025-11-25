import cloudinary
import cloudinary.uploader
import cloudinary.api
import os

# Configuración explícita con tu CLOUDINARY_URL
cloudinary.config(
    cloud_name="dsaqqwbdn",        # el nombre de tu cuenta
    api_key="967594418321858",     # tu API Key
    api_secret="jBjqm0rWf0e_Pup4aOtaVDtZB0o",  # tu API Secret
    secure=True
)

# Prueba de subida
result = cloudinary.uploader.upload(
    "https://cloudinary-devs.github.io/cld-docs-assets/assets/images/butterfly.jpeg",
    folder="biblioteca_plus"
)
print("URL subida:", result["secure_url"])
