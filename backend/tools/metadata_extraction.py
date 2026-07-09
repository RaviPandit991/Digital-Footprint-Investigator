"""Extract metadata from files (images, PDFs) via URL or local upload."""
import io
import os
import requests
from urllib.parse import urlparse

try:
    from PIL import Image
    from PIL.ExifTags import TAGS, GPSTAGS
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    from PyPDF2 import PdfReader
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False


def _extract_image_exif(data: bytes) -> dict:
    if not PIL_AVAILABLE:
        return {"error": "Pillow not installed."}
    try:
        img = Image.open(io.BytesIO(data))
    except Exception as e:
        return {"error": f"Not an image: {e}"}

    result = {
        "format": img.format,
        "mode": img.mode,
        "size": {"width": img.width, "height": img.height},
    }
    exif = getattr(img, "_getexif", lambda: None)()
    if not exif:
        result["exif"] = {}
        return result

    parsed = {}
    gps_data = {}
    for tag_id, value in exif.items():
        tag_name = TAGS.get(tag_id, str(tag_id))
        if tag_name == "GPSInfo":
            for gps_id, gps_val in value.items():
                gps_data[GPSTAGS.get(gps_id, str(gps_id))] = str(gps_val)
        else:
            v = str(value)
            if len(v) < 200:
                parsed[tag_name] = v
    result["exif"] = parsed
    if gps_data:
        result["gps"] = gps_data
        # Attempt to compute lat/lon
        try:
            lat = _dms_to_decimal(eval(gps_data.get("GPSLatitude", "()")), gps_data.get("GPSLatitudeRef"))
            lon = _dms_to_decimal(eval(gps_data.get("GPSLongitude", "()")), gps_data.get("GPSLongitudeRef"))
            if lat is not None and lon is not None:
                result["gps_coordinates"] = {"lat": lat, "lon": lon,
                                             "google_maps": f"https://maps.google.com/?q={lat},{lon}"}
        except Exception:
            pass
    return result


def _dms_to_decimal(dms, ref):
    if not dms or len(dms) < 3:
        return None
    try:
        deg = float(dms[0])
        minutes = float(dms[1]) / 60
        seconds = float(dms[2]) / 3600
        val = deg + minutes + seconds
        if ref in ("S", "W"):
            val = -val
        return round(val, 6)
    except Exception:
        return None


def _extract_pdf(data: bytes) -> dict:
    if not PDF_AVAILABLE:
        return {"error": "PyPDF2 not installed."}
    try:
        reader = PdfReader(io.BytesIO(data))
        info = reader.metadata or {}
        return {
            "num_pages": len(reader.pages),
            "metadata": {k.lstrip("/"): str(v) for k, v in info.items()},
            "encrypted": reader.is_encrypted,
        }
    except Exception as e:
        return {"error": f"PDF parse failed: {e}"}


def run(target: str, file_bytes: bytes = None, filename: str = None) -> dict:
    """Fetch a URL or use uploaded bytes and extract metadata."""
    if file_bytes:
        name = filename or "uploaded"
        data = file_bytes
    else:
        url = (target or "").strip()
        if not url:
            return {"error": "File URL or upload required."}
        if not url.startswith(("http://", "https://")):
            return {"error": "URL must start with http:// or https://"}
        try:
            r = requests.get(url, timeout=15, stream=True,
                             headers={"User-Agent": "DFI/1.0"})
            r.raise_for_status()
            data = r.content
            name = os.path.basename(urlparse(url).path) or "downloaded"
        except requests.RequestException as e:
            return {"error": f"Download failed: {e}"}

    ext = os.path.splitext(name)[1].lower()
    file_type = "unknown"
    metadata = {}

    if ext in (".jpg", ".jpeg", ".png", ".gif", ".tif", ".tiff", ".webp", ".heic"):
        file_type = "image"
        metadata = _extract_image_exif(data)
    elif ext == ".pdf":
        file_type = "pdf"
        metadata = _extract_pdf(data)
    else:
        # Try image first, then PDF
        img_result = _extract_image_exif(data)
        if "error" not in img_result:
            file_type = "image"
            metadata = img_result
        else:
            pdf_result = _extract_pdf(data)
            if "error" not in pdf_result:
                file_type = "pdf"
                metadata = pdf_result
            else:
                return {"error": f"Unsupported file type. Extension: {ext or 'none'}"}

    return {
        "filename": name,
        "file_type": file_type,
        "size_bytes": len(data),
        "metadata": metadata,
        "summary": f"{file_type.upper()} | {len(data)} bytes | "
                   f"{'GPS found!' if metadata.get('gps_coordinates') else 'No GPS'}"
    }
