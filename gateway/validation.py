#!/usr/bin/env python3
"""
Input Validation and Sanitization Module for OsMEN v3.0

Provides:
- JSON schema validation
- XSS protection (HTML escaping)
- SQL injection prevention
- Path traversal prevention
- Email/URL validation
- File upload validation
- Input length limits

Usage:
    from gateway.validation import InputValidator
    
    validator = InputValidator()
    clean_text = validator.sanitize_text(user_input)
    valid_email = validator.validate_email(email)
    safe_path = validator.validate_path(file_path)
"""

import re
import html
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union
from urllib.parse import urlparse
import unicodedata


# ==============================================================================
# Configuration
# ==============================================================================

@dataclass
class ValidationConfig:
    """Validation configuration"""
    max_string_length: int = 10000
    max_field_length: int = 255
    max_array_length: int = 1000
    max_json_depth: int = 10
    allowed_file_extensions: Set[str] = None
    allowed_domains: Set[str] = None
    blocked_patterns: List[str] = None
    
    def __post_init__(self):
        if self.allowed_file_extensions is None:
            self.allowed_file_extensions = {
                '.txt', '.pdf', '.doc', '.docx', '.xls', '.xlsx',
                '.png', '.jpg', '.jpeg', '.gif', '.svg',
                '.json', '.yaml', '.yml', '.csv', '.md'
            }
        
        if self.allowed_domains is None:
            self.allowed_domains = {
                'localhost', '127.0.0.1',
                'google.com', 'googleapis.com',
                'microsoft.com', 'outlook.com',
                'github.com', 'githubusercontent.com',
                'openai.com', 'anthropic.com'
            }
        
        if self.blocked_patterns is None:
            self.blocked_patterns = [
                r'<script[^>]*>',
                r'javascript:',
                r'on\w+\s*=',
                r'data:text/html',
            ]


# ==============================================================================
# Sanitizers
# ==============================================================================

class TextSanitizer:
    """Sanitizes text inputs"""
    
    # SQL keywords to detect
    SQL_KEYWORDS = {
        'select', 'insert', 'update', 'delete', 'drop', 'truncate',
        'alter', 'create', 'exec', 'execute', 'union', 'declare',
        'cast', 'convert', 'char', 'nchar', 'varchar', 'nvarchar'
    }
    
    # Patterns that might indicate injection attempts
    INJECTION_PATTERNS = [
        r"'(\s)*(or|and|union|select)",  # SQL injection
        r"--",  # SQL comment
        r";(\s)*$",  # SQL statement terminator
        r"\b(eval|exec|system|shell_exec|passthru)\s*\(",  # Code execution
        r"{{.*}}",  # Template injection
        r"\${.*}",  # Variable interpolation
    ]
    
    def __init__(self, config: Optional[ValidationConfig] = None):
        self.config = config or ValidationConfig()
        self._compiled_patterns = [
            re.compile(p, re.IGNORECASE) for p in self.INJECTION_PATTERNS
        ]
        self._blocked_patterns = [
            re.compile(p, re.IGNORECASE) for p in self.config.blocked_patterns
        ]
    
    def sanitize(self, text: str) -> str:
        """
        Sanitize text by escaping HTML and removing dangerous patterns
        
        Args:
            text: Input text
            
        Returns:
            Sanitized text
        """
        if not isinstance(text, str):
            return str(text)
        
        # Truncate if too long
        if len(text) > self.config.max_string_length:
            text = text[:self.config.max_string_length]
        
        # Normalize unicode
        text = unicodedata.normalize('NFKC', text)
        
        # Remove null bytes
        text = text.replace('\x00', '')
        
        # HTML escape
        text = html.escape(text, quote=True)
        
        return text
    
    def detect_injection(self, text: str) -> Optional[str]:
        """
        Detect potential injection attempts
        
        Args:
            text: Input text
            
        Returns:
            Name of detected pattern or None
        """
        if not isinstance(text, str):
            return None
        
        text_lower = text.lower()
        
        # Check for SQL keywords with suspicious context
        words = set(re.findall(r'\b\w+\b', text_lower))
        sql_matches = words.intersection(self.SQL_KEYWORDS)
        if len(sql_matches) >= 2:  # Multiple SQL keywords
            return "sql_keywords"
        
        # Check injection patterns
        for i, pattern in enumerate(self._compiled_patterns):
            if pattern.search(text):
                return f"injection_pattern_{i}"
        
        return None
    
    def detect_xss(self, text: str) -> bool:
        """
        Detect potential XSS attempts
        
        Args:
            text: Input text
            
        Returns:
            True if XSS patterns detected
        """
        if not isinstance(text, str):
            return False
        
        for pattern in self._blocked_patterns:
            if pattern.search(text):
                return True
        
        return False


# ==============================================================================
# Validators
# ==============================================================================

class EmailValidator:
    """Validates email addresses"""
    
    # RFC 5322 compliant (simplified)
    EMAIL_PATTERN = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    
    # Common disposable email domains
    DISPOSABLE_DOMAINS = {
        'tempmail.com', 'throwaway.email', 'mailinator.com',
        'guerrillamail.com', '10minutemail.com', 'temp-mail.org'
    }
    
    def validate(
        self,
        email: str,
        allow_disposable: bool = False
    ) -> tuple[bool, Optional[str]]:
        """
        Validate email address
        
        Args:
            email: Email address to validate
            allow_disposable: Whether to allow disposable emails
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not email or not isinstance(email, str):
            return False, "Email is required"
        
        email = email.strip().lower()
        
        # Check length
        if len(email) > 254:
            return False, "Email too long"
        
        # Check format
        if not self.EMAIL_PATTERN.match(email):
            return False, "Invalid email format"
        
        # Check domain
        domain = email.split('@')[1]
        
        if not allow_disposable and domain in self.DISPOSABLE_DOMAINS:
            return False, "Disposable email addresses not allowed"
        
        return True, None


class UrlValidator:
    """Validates URLs"""
    
    ALLOWED_SCHEMES = {'http', 'https'}
    
    def __init__(self, config: Optional[ValidationConfig] = None):
        self.config = config or ValidationConfig()
    
    def validate(
        self,
        url: str,
        require_https: bool = False,
        check_domain: bool = True
    ) -> tuple[bool, Optional[str]]:
        """
        Validate URL
        
        Args:
            url: URL to validate
            require_https: Require HTTPS scheme
            check_domain: Check against allowed domains
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not url or not isinstance(url, str):
            return False, "URL is required"
        
        try:
            parsed = urlparse(url)
        except Exception:
            return False, "Invalid URL format"
        
        # Check scheme
        if not parsed.scheme:
            return False, "URL scheme required"
        
        if parsed.scheme not in self.ALLOWED_SCHEMES:
            return False, f"Invalid scheme: {parsed.scheme}"
        
        if require_https and parsed.scheme != 'https':
            return False, "HTTPS required"
        
        # Check host
        if not parsed.netloc:
            return False, "URL host required"
        
        # Check domain allowlist
        if check_domain:
            host = parsed.netloc.split(':')[0].lower()
            domain_allowed = any(
                host == d or host.endswith('.' + d)
                for d in self.config.allowed_domains
            )
            if not domain_allowed:
                return False, f"Domain not allowed: {host}"
        
        return True, None


class PathValidator:
    """Validates file paths"""
    
    # Patterns that indicate path traversal
    TRAVERSAL_PATTERNS = [
        '..',
        '..\\',
        '../',
        '%2e%2e',
        '%252e%252e',
    ]
    
    def __init__(self, config: Optional[ValidationConfig] = None):
        self.config = config or ValidationConfig()
    
    def validate(
        self,
        path: str,
        base_dir: Optional[str] = None,
        check_extension: bool = True
    ) -> tuple[bool, Optional[str]]:
        """
        Validate file path
        
        Args:
            path: Path to validate
            base_dir: Base directory (path must be within)
            check_extension: Check against allowed extensions
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not path or not isinstance(path, str):
            return False, "Path is required"
        
        # Check for traversal patterns
        path_lower = path.lower()
        for pattern in self.TRAVERSAL_PATTERNS:
            if pattern in path_lower:
                return False, "Path traversal detected"
        
        try:
            # Normalize path
            normalized = os.path.normpath(path)
            
            # Check if path escapes base directory
            if base_dir:
                base_resolved = os.path.realpath(base_dir)
                path_resolved = os.path.realpath(
                    os.path.join(base_dir, normalized)
                )
                
                if not path_resolved.startswith(base_resolved):
                    return False, "Path escapes base directory"
            
            # Check extension
            if check_extension:
                ext = os.path.splitext(normalized)[1].lower()
                if ext and ext not in self.config.allowed_file_extensions:
                    return False, f"File extension not allowed: {ext}"
            
        except Exception as e:
            return False, f"Invalid path: {e}"
        
        return True, None
    
    def sanitize(self, path: str) -> str:
        """
        Sanitize a file path
        
        Args:
            path: Path to sanitize
            
        Returns:
            Sanitized path
        """
        # Remove null bytes
        path = path.replace('\x00', '')
        
        # Normalize
        path = os.path.normpath(path)
        
        # Remove leading slashes/backslashes
        path = path.lstrip('/\\')
        
        return path


class JsonValidator:
    """Validates JSON data"""
    
    def __init__(self, config: Optional[ValidationConfig] = None):
        self.config = config or ValidationConfig()
    
    def validate(
        self,
        data: Any,
        schema: Optional[Dict] = None,
        depth: int = 0
    ) -> tuple[bool, Optional[str]]:
        """
        Validate JSON data
        
        Args:
            data: Data to validate
            schema: Optional JSON schema
            depth: Current recursion depth
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check depth
        if depth > self.config.max_json_depth:
            return False, "JSON depth exceeded"
        
        # Validate based on type
        if isinstance(data, dict):
            if len(data) > self.config.max_array_length:
                return False, "Too many object keys"
            
            for key, value in data.items():
                if not isinstance(key, str):
                    return False, "Object keys must be strings"
                
                if len(key) > self.config.max_field_length:
                    return False, f"Key too long: {key[:20]}..."
                
                valid, error = self.validate(value, depth=depth + 1)
                if not valid:
                    return False, f"{key}: {error}"
        
        elif isinstance(data, list):
            if len(data) > self.config.max_array_length:
                return False, "Array too long"
            
            for i, item in enumerate(data):
                valid, error = self.validate(item, depth=depth + 1)
                if not valid:
                    return False, f"[{i}]: {error}"
        
        elif isinstance(data, str):
            if len(data) > self.config.max_string_length:
                return False, "String too long"
        
        # Validate against schema if provided
        if schema and depth == 0:
            return self._validate_schema(data, schema)
        
        return True, None
    
    def _validate_schema(
        self,
        data: Any,
        schema: Dict
    ) -> tuple[bool, Optional[str]]:
        """Validate data against JSON schema"""
        try:
            from jsonschema import validate, ValidationError
            validate(instance=data, schema=schema)
            return True, None
        except ImportError:
            # jsonschema not installed, skip validation
            return True, None
        except ValidationError as e:
            return False, str(e.message)
        except Exception as e:
            return False, str(e)


# ==============================================================================
# Combined Validator
# ==============================================================================

class InputValidator:
    """
    Combined input validator and sanitizer
    
    Usage:
        validator = InputValidator()
        
        # Sanitize text
        clean = validator.sanitize_text(user_input)
        
        # Validate email
        if not validator.validate_email(email):
            raise ValueError("Invalid email")
        
        # Validate URL
        if not validator.validate_url(url):
            raise ValueError("Invalid URL")
        
        # Validate path
        safe_path = validator.validate_path(path, base_dir="/uploads")
    """
    
    def __init__(self, config: Optional[ValidationConfig] = None):
        self.config = config or ValidationConfig()
        self.text_sanitizer = TextSanitizer(self.config)
        self.email_validator = EmailValidator()
        self.url_validator = UrlValidator(self.config)
        self.path_validator = PathValidator(self.config)
        self.json_validator = JsonValidator(self.config)
    
    def sanitize_text(self, text: str) -> str:
        """Sanitize text input"""
        return self.text_sanitizer.sanitize(text)
    
    def detect_injection(self, text: str) -> Optional[str]:
        """Detect potential injection attacks"""
        return self.text_sanitizer.detect_injection(text)
    
    def detect_xss(self, text: str) -> bool:
        """Detect potential XSS attacks"""
        return self.text_sanitizer.detect_xss(text)
    
    def validate_email(
        self,
        email: str,
        allow_disposable: bool = False
    ) -> bool:
        """Validate email address"""
        valid, _ = self.email_validator.validate(email, allow_disposable)
        return valid
    
    def validate_url(
        self,
        url: str,
        require_https: bool = False,
        check_domain: bool = True
    ) -> bool:
        """Validate URL"""
        valid, _ = self.url_validator.validate(url, require_https, check_domain)
        return valid
    
    def validate_path(
        self,
        path: str,
        base_dir: Optional[str] = None,
        check_extension: bool = True
    ) -> bool:
        """Validate file path"""
        valid, _ = self.path_validator.validate(path, base_dir, check_extension)
        return valid
    
    def sanitize_path(self, path: str) -> str:
        """Sanitize file path"""
        return self.path_validator.sanitize(path)
    
    def validate_json(
        self,
        data: Any,
        schema: Optional[Dict] = None
    ) -> bool:
        """Validate JSON data"""
        valid, _ = self.json_validator.validate(data, schema)
        return valid
    
    def sanitize_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively sanitize all string values in a dictionary
        
        Args:
            data: Dictionary to sanitize
            
        Returns:
            Sanitized dictionary
        """
        result = {}
        for key, value in data.items():
            if isinstance(value, str):
                result[key] = self.sanitize_text(value)
            elif isinstance(value, dict):
                result[key] = self.sanitize_dict(value)
            elif isinstance(value, list):
                result[key] = self.sanitize_list(value)
            else:
                result[key] = value
        return result
    
    def sanitize_list(self, data: List[Any]) -> List[Any]:
        """
        Recursively sanitize all string values in a list
        
        Args:
            data: List to sanitize
            
        Returns:
            Sanitized list
        """
        result = []
        for item in data:
            if isinstance(item, str):
                result.append(self.sanitize_text(item))
            elif isinstance(item, dict):
                result.append(self.sanitize_dict(item))
            elif isinstance(item, list):
                result.append(self.sanitize_list(item))
            else:
                result.append(item)
        return result


# ==============================================================================
# FastAPI Dependencies
# ==============================================================================

from fastapi import Depends, HTTPException, status


def get_validator() -> InputValidator:
    """Dependency injection for validator"""
    return InputValidator()


async def validate_request_body(
    body: Dict[str, Any],
    validator: InputValidator = Depends(get_validator)
) -> Dict[str, Any]:
    """
    Validate and sanitize request body
    
    Usage:
        @app.post("/api/endpoint")
        async def endpoint(body: Dict = Depends(validate_request_body)):
            # body is validated and sanitized
            pass
    """
    # Check for injection attempts
    def check_value(value: Any, path: str = ""):
        if isinstance(value, str):
            injection = validator.detect_injection(value)
            if injection:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid input at {path}: potential injection detected"
                )
            
            if validator.detect_xss(value):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid input at {path}: potential XSS detected"
                )
        
        elif isinstance(value, dict):
            for k, v in value.items():
                check_value(v, f"{path}.{k}" if path else k)
        
        elif isinstance(value, list):
            for i, v in enumerate(value):
                check_value(v, f"{path}[{i}]")
    
    check_value(body)
    
    # Validate JSON structure
    if not validator.validate_json(body):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON structure"
        )
    
    # Sanitize and return
    return validator.sanitize_dict(body)


# ==============================================================================
# Testing
# ==============================================================================

if __name__ == "__main__":
    print("Testing Input Validation Module...")
    
    validator = InputValidator()
    
    # Test text sanitization
    print("\n1. Text Sanitization:")
    test_texts = [
        "Hello, World!",
        "<script>alert('xss')</script>",
        "SELECT * FROM users WHERE 1=1",
        "Normal text with some 'quotes'",
    ]
    
    for text in test_texts:
        sanitized = validator.sanitize_text(text)
        injection = validator.detect_injection(text)
        xss = validator.detect_xss(text)
        print(f"  Input: {text[:50]}...")
        print(f"  Output: {sanitized[:50]}...")
        print(f"  Injection: {injection}, XSS: {xss}")
        print()
    
    # Test email validation
    print("2. Email Validation:")
    test_emails = [
        "valid@example.com",
        "invalid",
        "user@tempmail.com",
        "too@" + "a" * 250 + ".com",
    ]
    
    for email in test_emails:
        valid = validator.validate_email(email)
        print(f"  {email[:30]}: {'Valid' if valid else 'Invalid'}")
    
    # Test URL validation
    print("\n3. URL Validation:")
    test_urls = [
        "https://google.com/search",
        "http://evil-site.com/malware",
        "javascript:alert(1)",
        "https://github.com/repo",
    ]
    
    for url in test_urls:
        valid = validator.validate_url(url)
        print(f"  {url[:40]}: {'Valid' if valid else 'Invalid'}")
    
    # Test path validation
    print("\n4. Path Validation:")
    test_paths = [
        "file.txt",
        "../../../etc/passwd",
        "uploads/image.png",
        "document.exe",
    ]
    
    for path in test_paths:
        valid = validator.validate_path(path, base_dir="/app")
        print(f"  {path}: {'Valid' if valid else 'Invalid'}")
    
    # Test JSON validation
    print("\n5. JSON Validation:")
    test_json = {
        "name": "John <script>evil</script>",
        "nested": {
            "value": "SELECT * FROM users"
        },
        "list": ["item1", "item2"]
    }
    
    print(f"  Original: {test_json}")
    sanitized = validator.sanitize_dict(test_json)
    print(f"  Sanitized: {sanitized}")
    
    print("\n✅ Input validation module working!")
