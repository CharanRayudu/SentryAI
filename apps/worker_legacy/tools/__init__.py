"""
SentryAI Tool Management

This package handles security tool integration:

- auto_documenter: Automatically generates tool definitions from --help output
- Tool registry for managing installed tools
- Command building from structured arguments
"""
from .auto_documenter import (
    ParamType,
    ToolParameter,
    ToolDefinition,
    AutoDocumenter,
    ToolRegistry,
    BUILTIN_DEFINITIONS,
    get_builtin_definition,
)

__all__ = [
    "ParamType",
    "ToolParameter",
    "ToolDefinition",
    "AutoDocumenter",
    "ToolRegistry",
    "BUILTIN_DEFINITIONS",
    "get_builtin_definition",
]

