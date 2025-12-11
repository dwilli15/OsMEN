"""
ConvertX Utilities - Format helpers and common conversions
==========================================================
"""

from typing import Dict, List, Optional, Set

# Common format conversions by category
COMMON_CONVERSIONS: Dict[str, Dict[str, List[str]]] = {
    "video": {
        "mp4": ["webm", "avi", "mkv", "mov", "gif", "mp3", "wav"],
        "mkv": ["mp4", "webm", "avi", "mp3"],
        "avi": ["mp4", "mkv", "webm"],
        "webm": ["mp4", "mkv", "gif"],
        "mov": ["mp4", "mkv", "webm", "gif"],
    },
    "audio": {
        "mp3": ["wav", "flac", "ogg", "m4a", "aac"],
        "wav": ["mp3", "flac", "ogg", "m4a"],
        "flac": ["mp3", "wav", "ogg", "m4a"],
        "ogg": ["mp3", "wav", "flac"],
        "m4a": ["mp3", "wav", "flac", "ogg"],
    },
    "image": {
        "jpg": ["png", "webp", "gif", "pdf", "avif", "heic"],
        "jpeg": ["png", "webp", "gif", "pdf", "avif", "heic"],
        "png": ["jpg", "webp", "gif", "pdf", "avif", "ico"],
        "webp": ["jpg", "png", "gif", "pdf"],
        "gif": ["mp4", "webm", "png", "jpg"],
        "heic": ["jpg", "png", "webp"],
        "avif": ["jpg", "png", "webp"],
        "svg": ["png", "pdf", "jpg"],
        "tiff": ["jpg", "png", "pdf"],
        "bmp": ["jpg", "png", "webp"],
    },
    "document": {
        "pdf": ["docx", "txt", "html", "epub", "md"],
        "docx": ["pdf", "txt", "html", "md", "odt"],
        "doc": ["pdf", "docx", "txt", "html"],
        "odt": ["pdf", "docx", "txt"],
        "txt": ["pdf", "docx", "html", "md"],
        "md": ["pdf", "html", "docx", "txt"],
        "html": ["pdf", "docx", "md", "txt"],
        "rtf": ["pdf", "docx", "txt"],
        "tex": ["pdf"],
    },
    "ebook": {
        "epub": ["mobi", "pdf", "azw3", "html"],
        "mobi": ["epub", "pdf", "azw3"],
        "azw3": ["epub", "mobi", "pdf"],
        "fb2": ["epub", "mobi", "pdf"],
    },
    "3d": {
        "obj": ["stl", "fbx", "gltf", "glb", "dae"],
        "stl": ["obj", "fbx", "gltf"],
        "fbx": ["obj", "stl", "gltf", "glb"],
        "gltf": ["obj", "stl", "fbx", "glb"],
        "glb": ["obj", "stl", "gltf"],
        "dae": ["obj", "fbx", "gltf"],
    },
}

# Format aliases (map alternative names to canonical names)
FORMAT_ALIASES: Dict[str, str] = {
    "jpeg": "jpg",
    "tif": "tiff",
    "htm": "html",
    "markdown": "md",
    "wave": "wav",
    "aiff": "aif",
}

# All supported input formats by category
SUPPORTED_INPUT_FORMATS: Dict[str, Set[str]] = {
    "video": {
        "mp4",
        "mkv",
        "avi",
        "webm",
        "mov",
        "flv",
        "wmv",
        "m4v",
        "mpeg",
        "3gp",
        "ts",
    },
    "audio": {"mp3", "wav", "flac", "ogg", "m4a", "aac", "wma", "aiff", "ape", "opus"},
    "image": {
        "jpg",
        "jpeg",
        "png",
        "gif",
        "webp",
        "svg",
        "bmp",
        "tiff",
        "heic",
        "heif",
        "avif",
        "ico",
        "psd",
        "raw",
    },
    "document": {
        "pdf",
        "docx",
        "doc",
        "odt",
        "txt",
        "md",
        "html",
        "rtf",
        "tex",
        "epub",
        "rst",
        "csv",
    },
    "ebook": {"epub", "mobi", "azw3", "fb2", "lit", "pdb"},
    "3d": {"obj", "stl", "fbx", "gltf", "glb", "dae", "3ds", "blend", "ply", "x3d"},
}

# All supported output formats by category
SUPPORTED_OUTPUT_FORMATS: Dict[str, Set[str]] = {
    "video": {"mp4", "mkv", "avi", "webm", "mov", "gif", "ts"},
    "audio": {"mp3", "wav", "flac", "ogg", "m4a", "aac", "opus"},
    "image": {"jpg", "png", "gif", "webp", "pdf", "avif", "ico", "tiff", "bmp"},
    "document": {"pdf", "docx", "txt", "html", "md", "odt", "rtf", "epub"},
    "ebook": {"epub", "mobi", "azw3", "pdf", "html"},
    "3d": {"obj", "stl", "fbx", "gltf", "glb", "dae"},
}


def normalize_format(format_str: str) -> str:
    """
    Normalize a format string to its canonical form.

    Args:
        format_str: Format extension (with or without dot)

    Returns:
        Normalized format string (lowercase, no dot)
    """
    fmt = format_str.lower().lstrip(".")
    return FORMAT_ALIASES.get(fmt, fmt)


def get_category(format_str: str) -> Optional[str]:
    """
    Get the category for a given format.

    Args:
        format_str: Format extension

    Returns:
        Category name or None if unknown
    """
    fmt = normalize_format(format_str)

    for category, formats in SUPPORTED_INPUT_FORMATS.items():
        if fmt in formats:
            return category

    for category, formats in SUPPORTED_OUTPUT_FORMATS.items():
        if fmt in formats:
            return category

    return None


def is_format_supported(format_str: str, as_input: bool = True) -> bool:
    """
    Check if a format is supported.

    Args:
        format_str: Format extension
        as_input: Check as input format (True) or output format (False)

    Returns:
        True if format is supported
    """
    fmt = normalize_format(format_str)
    formats_dict = SUPPORTED_INPUT_FORMATS if as_input else SUPPORTED_OUTPUT_FORMATS

    for formats in formats_dict.values():
        if fmt in formats:
            return True

    return False


def get_possible_conversions(input_format: str) -> List[str]:
    """
    Get list of possible output formats for a given input format.

    Args:
        input_format: Input format extension

    Returns:
        List of possible output formats
    """
    fmt = normalize_format(input_format)

    # Check common conversions first
    for category_conversions in COMMON_CONVERSIONS.values():
        if fmt in category_conversions:
            return category_conversions[fmt]

    # Fall back to same-category outputs
    category = get_category(fmt)
    if category and category in SUPPORTED_OUTPUT_FORMATS:
        outputs = list(SUPPORTED_OUTPUT_FORMATS[category])
        # Remove the input format from outputs
        if fmt in outputs:
            outputs.remove(fmt)
        return outputs

    return []


def suggest_conversion(input_format: str, purpose: str = "general") -> Optional[str]:
    """
    Suggest the best output format based on purpose.

    Args:
        input_format: Input format extension
        purpose: Purpose of conversion ('web', 'archive', 'print', 'general')

    Returns:
        Suggested output format or None
    """
    fmt = normalize_format(input_format)
    category = get_category(fmt)

    suggestions = {
        "web": {
            "video": "webm",
            "audio": "mp3",
            "image": "webp",
            "document": "html",
        },
        "archive": {
            "video": "mkv",
            "audio": "flac",
            "image": "png",
            "document": "pdf",
        },
        "print": {
            "video": None,
            "audio": None,
            "image": "pdf",
            "document": "pdf",
        },
        "general": {
            "video": "mp4",
            "audio": "mp3",
            "image": "jpg",
            "document": "pdf",
            "ebook": "epub",
            "3d": "gltf",
        },
    }

    purpose_map = suggestions.get(purpose, suggestions["general"])
    return purpose_map.get(category)


def estimate_conversion_time(
    input_format: str,
    output_format: str,
    file_size_mb: float,
) -> float:
    """
    Estimate conversion time in seconds.

    Args:
        input_format: Input format
        output_format: Output format
        file_size_mb: File size in megabytes

    Returns:
        Estimated time in seconds
    """
    # Base time estimates per category (seconds per MB)
    category_times = {
        "video": 2.0,  # Video transcoding is slow
        "audio": 0.5,
        "image": 0.1,
        "document": 0.3,
        "ebook": 0.5,
        "3d": 1.0,
    }

    input_category = get_category(input_format)
    base_time = category_times.get(input_category, 1.0)

    # Add overhead for format complexity
    complex_outputs = {"pdf", "epub", "mkv"}
    if normalize_format(output_format) in complex_outputs:
        base_time *= 1.5

    return base_time * file_size_mb + 1.0  # Minimum 1 second


def batch_conversion_plan(
    files: List[str],
    target_format: str,
) -> List[Dict]:
    """
    Create a plan for batch file conversion.

    Args:
        files: List of file paths
        target_format: Target format for all files

    Returns:
        List of conversion plan dicts
    """
    from pathlib import Path

    plan = []
    for file_path in files:
        path = Path(file_path)
        input_format = path.suffix.lstrip(".")

        plan.append(
            {
                "input": str(path),
                "output": str(path.with_suffix(f".{normalize_format(target_format)}")),
                "input_format": normalize_format(input_format),
                "output_format": normalize_format(target_format),
                "supported": is_format_supported(input_format)
                and target_format in get_possible_conversions(input_format),
            }
        )

    return plan
