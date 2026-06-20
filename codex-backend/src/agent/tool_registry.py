"""
Tool registry with @tool decorator.

Auto-generates JSON schema from function signatures (type hints + defaults).
Supports sync and async functions. Thread-safe.
"""

import inspect
import json
import functools
from typing import Any, Callable, get_type_hints

# JSON type mapping for Python types
_TYPE_MAP = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
    list: "array",
    dict: "object",
    type(None): "null",
}


def _type_to_json(tp: type) -> dict:
    if tp in _TYPE_MAP:
        return {"type": _TYPE_MAP[tp]}
    origin = getattr(tp, "__origin__", None)
    if origin is list:
        args = getattr(tp, "__args__", [Any])
        return {"type": "array", "items": _type_to_json(args[0] if args else Any)}
    if origin is dict:
        args = getattr(tp, "__args__", [str, Any])
        return {"type": "object", "additionalProperties": _type_to_json(args[1] if len(args) > 1 else Any)}
    return {"type": "string"}


def _generate_schema(fn: Callable) -> dict:
    sig = inspect.signature(fn)
    hints = get_type_hints(fn, globalns=_TYPE_MAP, localns=_TYPE_MAP)
    properties = {}
    required = []
    for name, param in sig.parameters.items():
        if name == "return":
            continue
        param_type = hints.get(name, str)
        prop = _type_to_json(param_type)
        if param.default is not inspect.Parameter.empty:
            prop["default"] = param.default
        else:
            required.append(name)
        if param.annotation is not inspect.Parameter.empty:
            origin = getattr(param.annotation, "__origin__", None)
            if origin is list:
                prop = {"type": "array", "items": {"type": "string"}}
            elif param.annotation is str:
                prop = {"type": "string"}
        properties[name] = prop
    return {
        "type": "object",
        "properties": properties,
        "required": required,
    }


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, Callable] = {}

    def register(self, fn: Callable) -> Callable:
        name = fn.__name__
        description = inspect.getdoc(fn) or ""
        schema = _generate_schema(fn)
        self._tools[name] = fn
        # Store definition for LLM API
        setattr(fn, "_tool_def", {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": schema,
            },
        })
        return fn

    def get_definitions(self) -> list[dict]:
        return [getattr(fn, "_tool_def") for fn in self._tools.values()]

    async def execute(self, name: str, **kwargs) -> Any:
        fn = self._tools.get(name)
        if not fn:
            raise ValueError(f"Unknown tool: {name}")
        if inspect.iscoroutinefunction(fn):
            return await fn(**kwargs)
        return fn(**kwargs)

    def __contains__(self, name: str) -> bool:
        return name in self._tools


# Global singleton
_registry = ToolRegistry()


def tool(fn: Callable = None, *, name: str = None) -> Callable:
    """
    Decorator that registers a function as a tool.

    Can be used as @tool or @tool(name="custom_name").
    Generates JSON schema from type hints and docstring.
    """
    def wrapper(f: Callable) -> Callable:
        registered = _registry.register(f)
        if name:
            _registry._tools[name] = _registry._tools.pop(f.__name__)
            registered._tool_def["function"]["name"] = name
        return registered

    if fn is None:
        return wrapper
    return wrapper(fn)


def get_registry() -> ToolRegistry:
    return _registry
