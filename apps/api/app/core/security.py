"""
Security Middleware & Validation
Command sanitization and input validation for SentryAI
"""
import re
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from pydantic import BaseModel


# --- Forbidden Patterns ---

# Shell injection patterns
SHELL_INJECTION_PATTERNS = [
    r';',           # Command chaining
    r'\|',          # Pipe
    r'&&',          # AND operator
    r'\|\|',        # OR operator
    r'`',           # Backtick execution
    r'\$\(',        # Command substitution
    r'\$\{',        # Variable expansion
    r'>',           # Output redirection
    r'<',           # Input redirection
    r'\n',          # Newline injection
    r'\r',          # Carriage return
    r'\\',          # Escape sequences
]

# Dangerous commands
DANGEROUS_COMMANDS = [
    'rm', 'rmdir', 'del', 'format',
    'dd', 'mkfs', 'fdisk',
    'shutdown', 'reboot', 'halt', 'poweroff',
    'chmod', 'chown', 'chgrp',
    'passwd', 'useradd', 'userdel',
    'sudo', 'su', 'doas',
    'curl', 'wget', 'nc', 'netcat',  # Network tools (use approved wrappers)
    'python', 'python3', 'perl', 'ruby', 'php', 'node',  # Interpreters
    'eval', 'exec', 'source',
    'export', 'env', 'set',
    'kill', 'pkill', 'killall',
    'crontab', 'at',
]

# Path traversal patterns
PATH_TRAVERSAL_PATTERNS = [
    r'\.\.',           # Parent directory
    r'\./',            # Current directory explicit
    r'^/',             # Absolute path (Linux)
    r'^[A-Za-z]:',     # Absolute path (Windows)
    r'~',              # Home directory
]

# SQL injection patterns (for any raw queries)
SQL_INJECTION_PATTERNS = [
    r"'",              # Single quote
    r'"',              # Double quote
    r'--',             # SQL comment
    r'/\*',            # Block comment start
    r'\*/',            # Block comment end
    r';\s*$',          # Statement terminator
]


class SecurityViolation(BaseModel):
    """Security violation response"""
    error: str = "SecurityViolation"
    message: str
    pattern: Optional[str] = None
    input_preview: Optional[str] = None


class CommandValidator:
    """Validates and sanitizes shell commands"""
    
    def __init__(
        self,
        allow_custom_args: bool = True,
        allowed_tools: Optional[List[str]] = None
    ):
        self.allow_custom_args = allow_custom_args
        self.allowed_tools = allowed_tools or [
            # ProjectDiscovery tools
            'nuclei', 'subfinder', 'naabu', 'httpx', 'dnsx', 'katana',
            # Standard tools
            'nmap', 'masscan', 'nikto', 'gobuster', 'ffuf', 'wfuzz',
            'sqlmap', 'whatweb', 'wafw00f',
            # Utilities
            'dig', 'host', 'whois', 'traceroute',
        ]
    
    def validate(self, command: str) -> Tuple[bool, Optional[SecurityViolation]]:
        """
        Validate a command string.
        
        Returns:
            Tuple of (is_valid, violation_or_none)
        """
        if not command or not command.strip():
            return False, SecurityViolation(
                message="Empty command"
            )
        
        # Check for shell injection
        for pattern in SHELL_INJECTION_PATTERNS:
            if re.search(pattern, command):
                return False, SecurityViolation(
                    message="Command contained forbidden characters",
                    pattern=pattern,
                    input_preview=command[:50] + "..." if len(command) > 50 else command
                )
        
        # Parse command parts
        parts = command.strip().split()
        if not parts:
            return False, SecurityViolation(message="Invalid command format")
        
        tool = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        # Check if tool is allowed
        if tool not in self.allowed_tools:
            return False, SecurityViolation(
                message=f"Tool '{tool}' is not in the approved list",
                input_preview=tool
            )
        
        # Check for dangerous commands in arguments
        for arg in args:
            arg_lower = arg.lower()
            for dangerous in DANGEROUS_COMMANDS:
                if dangerous in arg_lower:
                    return False, SecurityViolation(
                        message=f"Argument contains forbidden command: {dangerous}",
                        pattern=dangerous,
                        input_preview=arg[:30]
                    )
        
        # Check for path traversal in arguments
        for arg in args:
            for pattern in PATH_TRAVERSAL_PATTERNS:
                if re.search(pattern, arg):
                    return False, SecurityViolation(
                        message="Path traversal attempt detected",
                        pattern=pattern,
                        input_preview=arg[:30]
                    )
        
        return True, None
    
    def sanitize(self, command: str) -> str:
        """
        Sanitize a command string by removing potentially dangerous parts.
        Note: This is a last resort - validation should be preferred.
        """
        # Remove null bytes
        command = command.replace('\x00', '')
        
        # Remove shell metacharacters
        for char in [';', '|', '&', '`', '$', '>', '<', '\n', '\r']:
            command = command.replace(char, '')
        
        # Remove multiple spaces
        command = ' '.join(command.split())
        
        return command.strip()


class InputValidator:
    """General input validation"""
    
    @staticmethod
    def validate_target(target: str) -> Tuple[bool, Optional[str]]:
        """Validate a scan target (domain, IP, URL)"""
        if not target or not target.strip():
            return False, "Target cannot be empty"
        
        # Length check
        if len(target) > 2000:
            return False, "Target too long"
        
        # Check for shell injection in target
        for pattern in SHELL_INJECTION_PATTERNS:
            if re.search(pattern, target):
                return False, f"Invalid characters in target"
        
        # Basic format validation
        # Allow: domains, IPs, URLs, CIDR notation, wildcards
        valid_pattern = r'^[\w\.\-\:\/\*\@]+$'
        if not re.match(valid_pattern, target):
            return False, "Invalid target format"
        
        return True, None
    
    @staticmethod
    def validate_cron(expression: str) -> Tuple[bool, Optional[str]]:
        """Validate a cron expression"""
        if not expression:
            return False, "Cron expression cannot be empty"
        
        parts = expression.split()
        if len(parts) != 5:
            return False, "Invalid cron format (expected 5 fields)"
        
        # Basic validation for each field
        ranges = [
            (0, 59),   # Minute
            (0, 23),   # Hour
            (1, 31),   # Day of month
            (1, 12),   # Month
            (0, 7),    # Day of week (0 and 7 = Sunday)
        ]
        
        for i, (part, (min_val, max_val)) in enumerate(zip(parts, ranges)):
            if part == '*':
                continue
            
            # Handle ranges and steps
            part = part.replace('*/', '').replace('-', ',').replace('/', ',')
            
            for val in part.split(','):
                if val.isdigit():
                    num = int(val)
                    if num < min_val or num > max_val:
                        return False, f"Value {num} out of range for field {i+1}"
        
        return True, None
    
    @staticmethod
    def validate_webhook_url(url: str) -> Tuple[bool, Optional[str]]:
        """Validate a webhook URL"""
        if not url:
            return False, "URL cannot be empty"
        
        # Must be HTTPS (or HTTP for local development)
        if not url.startswith(('https://', 'http://localhost', 'http://127.0.0.1')):
            return False, "Webhook URL must use HTTPS"
        
        # Length check
        if len(url) > 2000:
            return False, "URL too long"
        
        # Basic URL format
        url_pattern = r'^https?://[\w\-\.]+(:\d+)?(/[\w\-\./\?\&\=\%]*)?$'
        if not re.match(url_pattern, url):
            return False, "Invalid URL format"
        
        return True, None


def raise_security_violation(violation: SecurityViolation):
    """Raise HTTP exception for security violation"""
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={
            "error": violation.error,
            "message": violation.message,
            "pattern": violation.pattern
        }
    )


# --- FastAPI Dependency ---

def get_command_validator(
    allowed_tools: Optional[List[str]] = None
) -> CommandValidator:
    """Dependency to get command validator"""
    return CommandValidator(allowed_tools=allowed_tools)


# Singleton instances
command_validator = CommandValidator()
input_validator = InputValidator()

