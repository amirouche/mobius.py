#!/usr/bin/env python3
"""
aston.py - AST Object Notation converter

Converts Python source files to ASTON representation (tuples of content-addressed AST nodes).

Format: Each line is a JSON array representing a tuple (content_hash, key, index, value)
- content_hash: SHA256 hex digest of the canonical JSON representation
- key: Field name within the object
- index: Position in array (int) or None for scalar values
- value: Atomic data (None/str/int/float/bool) or hash reference (HC)
"""

import ast
import hashlib
import json
import sys
from typing import Any, List, Tuple


def ast_to_aston(node: ast.AST) -> Tuple[str, List[Tuple]]:
    """Convert an AST node to ASTON tuples.

    Args:
        node: AST node to convert

    Returns:
        (content_hash, all_tuples) where:
        - content_hash: SHA256 hex digest of the canonical JSON representation
        - all_tuples: List of (content_hash, key, index, value) tuples for this node and all descendants
    """
    all_tuples = []
    obj = {'_type': node.__class__.__name__}

    # Process all fields and build obj for hashing
    field_data = {}

    for field, value in ast.iter_fields(node):
        if value is None:
            obj[field] = None
            field_data[field] = ('scalar', None)
        elif isinstance(value, (str, int, float, bool)):
            obj[field] = value
            field_data[field] = ('scalar', value)
        elif isinstance(value, list):
            obj[field] = []
            list_items = []
            for item in value:
                if isinstance(item, ast.AST):
                    child_hash, child_tuples = ast_to_aston(item)
                    all_tuples.extend(child_tuples)
                    obj[field].append(child_hash)
                    list_items.append(child_hash)
                else:
                    obj[field].append(item)
                    list_items.append(item)
            field_data[field] = ('list', list_items)
        elif isinstance(value, ast.AST):
            child_hash, child_tuples = ast_to_aston(value)
            all_tuples.extend(child_tuples)
            obj[field] = child_hash
            field_data[field] = ('scalar', child_hash)

    # Compute content hash from canonical JSON representation
    canonical = json.dumps(obj, sort_keys=True, ensure_ascii=False)
    content_hash = hashlib.sha256(canonical.encode('utf-8')).hexdigest()

    # Create tuples for this node
    node_tuples = [(content_hash, '_type', None, node.__class__.__name__)]

    for field, (kind, data) in field_data.items():
        if kind == 'scalar':
            node_tuples.append((content_hash, field, None, data))
        elif kind == 'list':
            for i, item_value in enumerate(data):
                node_tuples.append((content_hash, field, i, item_value))

    all_tuples.extend(node_tuples)
    return content_hash, all_tuples


def main():
    """Main CLI entry point."""
    if len(sys.argv) != 2:
        print("Usage: aston.py <filepath>", file=sys.stderr)
        sys.exit(1)

    filepath = sys.argv[1]

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()
    except FileNotFoundError:
        print(f"Error: File not found: {filepath}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        print(f"Syntax error in {filepath}: {e}", file=sys.stderr)
        sys.exit(1)

    _, tuples = ast_to_aston(tree)

    # Output as JSON lines
    for tup in tuples:
        print(json.dumps(tup, ensure_ascii=False))


if __name__ == '__main__':
    main()
