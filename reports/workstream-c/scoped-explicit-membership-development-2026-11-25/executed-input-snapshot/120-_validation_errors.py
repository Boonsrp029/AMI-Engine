"""Public validation errors without rejected values or exception context."""

# Only application-defined field names can be reflected. Extra-field names are
# user input too: omitting just Pydantic's `input` would still disclose them.
_FIELDS = frozenset({
    "body", "path", "query", "header", "cookie", "request_key", "revision",
    "draft", "title", "claims", "text", "source_ids", "warnings", "decision",
    "reviewer", "support_confirmed", "note", "task_seconds", "manual_seconds",
    "usefulness", "run_id",
})
_MESSAGES = {
    "missing": "Field required",
    "extra_forbidden": "Unexpected field",
    "json_invalid": "Invalid JSON body",
    "json_type": "Invalid JSON body",
    "string_type": "Enter text",
    "string_too_short": "Text is shorter than the field permits",
    "string_too_long": "Text is longer than the field permits",
    "string_pattern_mismatch": "Text has an unsupported format",
    "int_type": "Enter a whole number",
    "int_parsing": "Enter a whole number",
    "float_type": "Enter a number",
    "float_parsing": "Enter a number",
    "bool_type": "Enter true or false",
    "bool_parsing": "Enter true or false",
    "list_type": "Enter a list",
    "too_short": "Too few items",
    "too_long": "Too many items",
    "greater_than_equal": "Number is below the permitted minimum",
    "less_than_equal": "Number exceeds the permitted maximum",
    "finite_number": "Enter a finite number",
    "literal_error": "Choose a permitted value",
    "model_attributes_type": "Enter an object with the required fields",
    "value_error": "Invalid field value",
}


def public_validation_details(errors):
    """Keep the 422 detail envelope; never stringify supplied data or errors."""
    details = []
    for error in errors:
        kind = error.get("type")
        kind = kind if isinstance(kind, str) and kind in _MESSAGES else "value_error"
        location = error.get("loc", ())
        location = location if isinstance(location, (tuple, list)) else ()
        safe_location = [part if (type(part) is int and part >= 0) or
                         (type(part) is str and part in _FIELDS) else "field" for part in location]
        message = _MESSAGES[kind]
        if kind == "value_error" and safe_location == ["body", "query"]:
            message = "Enter a public research question without personal contact or identity information"
        details.append({"type": kind, "loc": safe_location, "msg": message})
    return details
