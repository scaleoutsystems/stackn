from django.core.exceptions import ValidationError


def validate_image_content_type(image):
    if image.content_type not in ["image/jpeg", "image/png"]:
        raise ValidationError(
            code="unsupported_content_type" "Unsupported content type"
        )
