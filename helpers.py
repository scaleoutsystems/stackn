import base64
import re


def urlify(s):
    # Remove all non-word characters (everything except numbers and letters)
    s = re.sub(r"[^\w\s]", "", s)

    # Replace all runs of whitespace with a single dash
    s = re.sub(r"\s+", "-", s)

    return s


def get_minio_keys(project):
    return {
        "project_key": decrypt_key(project.project_key),
        "project_secret": decrypt_key(project.project_secret),
    }


def decrypt_key(key):
    base64_bytes = key.encode("ascii")
    result = base64.b64decode(base64_bytes)
    return result.decode("ascii")
