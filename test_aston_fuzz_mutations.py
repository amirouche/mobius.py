#!/usr/bin/env python3
"""
Mutation-based fuzz testing for aston.py round-trip correctness.

Generates deterministic mutations of Python code from a seed and verifies
that aston_read(aston_write(ast)) == ast for all mutations.
"""

import ast
import hashlib
import random
import sys
import traceback
from pathlib import Path
from typing import List, Tuple

# Import from aston.py
from aston import aston_write, aston_read


# Base corpus for mutations
BASE_CORPUS = [
    "x = 1",
    "def f(): pass",
    "def f(x): return x",
    "def f(x, y): return x + y",
    "class C: pass",
    "for i in range(10): pass",
    "if x: pass",
    "[x for x in range(10)]",
    "lambda x: x + 1",
    "x, y = 1, 2",
    "def f():\n    '''Docstring'''\n    return 42",
    "class C:\n    def method(self): return 1",
]


# Common modules for import mutations
IMPORT_MODULES = [
    "os",
    "sys",
    "re",
    "json",
    "math",
    "random",
    "pathlib",
    "collections",
    "itertools",
    "functools",
    "typing",
    "datetime",
    "hashlib",
    "urllib",
    "abc",
]

IMPORT_ITEMS = {
    "os": ["path", "environ", "getcwd", "listdir"],
    "sys": ["argv", "exit", "stdout", "stderr"],
    "collections": ["Counter", "defaultdict", "OrderedDict", "namedtuple"],
    "typing": ["List", "Dict", "Tuple", "Optional", "Union"],
    "pathlib": ["Path", "PurePath"],
    "itertools": ["chain", "cycle", "repeat", "islice"],
    "functools": ["reduce", "partial", "lru_cache"],
    "datetime": ["datetime", "date", "time", "timedelta"],
}


def mutate_add_imports(code: str, rng: random.Random) -> str:
    """Add random import statements to code."""
    mutations = []

    # Add 1-5 random imports
    num_imports = rng.randint(1, 5)

    for _ in range(num_imports):
        mutation_type = rng.choice(["import", "from_import", "from_import_as"])

        if mutation_type == "import":
            # import module
            module = rng.choice(IMPORT_MODULES)
            mutations.append(f"import {module}")

        elif mutation_type == "from_import":
            # from module import item
            module = rng.choice([m for m in IMPORT_MODULES if m in IMPORT_ITEMS])
            items = IMPORT_ITEMS[module]
            item = rng.choice(items)
            mutations.append(f"from {module} import {item}")

        elif mutation_type == "from_import_as":
            # from module import item as alias
            module = rng.choice([m for m in IMPORT_MODULES if m in IMPORT_ITEMS])
            items = IMPORT_ITEMS[module]
            item = rng.choice(items)
            alias = f"{item}_alias_{rng.randint(0, 999)}"
            mutations.append(f"from {module} import {item} as {alias}")

    # Combine imports with original code
    import_block = "\n".join(mutations)
    return f"{import_block}\n\n{code}"


def mutate_add_docstring(code: str, rng: random.Random) -> str:
    """Add docstrings to functions/classes."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return code

    # Find functions and classes without docstrings
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            # Check if already has docstring
            if (node.body and
                isinstance(node.body[0], ast.Expr) and
                isinstance(node.body[0].value, ast.Constant) and
                isinstance(node.body[0].value.value, str)):
                continue  # Already has docstring

            # Add random docstring
            if rng.random() < 0.5:
                docstrings = [
                    "Documentation string.",
                    "This is a function.",
                    "Returns a value.",
                    "Performs an operation.",
                ]
                docstring = rng.choice(docstrings)
                doc_node = ast.Expr(value=ast.Constant(value=docstring))
                node.body.insert(0, doc_node)

    return ast.unparse(tree)


def mutate_add_type_hints(code: str, rng: random.Random) -> str:
    """Add random type hints to function parameters."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return code

    type_hints = ["int", "str", "float", "bool", "List", "Dict"]

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Add type hints to arguments
            for arg in node.args.args:
                if arg.annotation is None and rng.random() < 0.3:
                    hint = rng.choice(type_hints)
                    arg.annotation = ast.Name(id=hint, ctx=ast.Load())

            # Add return type hint
            if node.returns is None and rng.random() < 0.3:
                hint = rng.choice(type_hints)
                node.returns = ast.Name(id=hint, ctx=ast.Load())

    ast.fix_missing_locations(tree)
    return ast.unparse(tree)


def mutate_code(code: str, seed: int) -> str:
    """Apply deterministic mutations to code based on seed.

    Returns mutated code that is still valid Python.
    """
    rng = random.Random(seed)

    # Apply mutations in sequence
    mutated = code

    # Always add imports
    mutated = mutate_add_imports(mutated, rng)

    # Maybe add docstrings
    if rng.random() < 0.5:
        mutated = mutate_add_docstring(mutated, rng)

    # Maybe add type hints
    if rng.random() < 0.3:
        mutated = mutate_add_type_hints(mutated, rng)

    # Verify it's still valid Python
    try:
        ast.parse(mutated)
        return mutated
    except SyntaxError:
        # If mutation broke syntax, return original
        return code


def test_mutation(code: str, seed: int, mutation_id: str) -> Tuple[bool, str, str]:
    """Test a single code mutation for round-trip correctness.

    Returns:
        (success, error_message, mutated_code)
    """
    try:
        # Generate mutation
        mutated_code = mutate_code(code, seed)

        # Parse original
        tree = ast.parse(mutated_code)

        # Convert to ASTON and back
        _, tuples = aston_write(tree)
        reconstructed = aston_read(tuples)

        # Compare using ast.dump
        original_dump = ast.dump(tree)
        reconstructed_dump = ast.dump(reconstructed)

        if original_dump != reconstructed_dump:
            return False, "AST mismatch", mutated_code

        return True, "", mutated_code

    except Exception as e:
        return False, f"{type(e).__name__}: {e}\n{traceback.format_exc()}", mutated_code


def save_failure(mutated_code: str, seed: int, base_idx: int) -> str:
    """Save failing code to /tmp and return filepath."""
    # Create unique filename based on seed and base index
    filename = f"/tmp/aston_fuzz_fail_base{base_idx}_seed{seed}.py"

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(mutated_code)

    return filename


def main():
    """Run mutation-based fuzz tests."""
    # Parse command line arguments
    if len(sys.argv) > 1:
        try:
            seed = int(sys.argv[1])
            num_mutations = int(sys.argv[2]) if len(sys.argv) > 2 else 1
            print(f"Running with seed={seed}, mutations={num_mutations}")
            seeds = [seed + i for i in range(num_mutations)]
        except ValueError:
            print("Usage: test_aston_fuzz_mutations.py [seed] [num_mutations]", file=sys.stderr)
            print("  seed: Starting seed for RNG (default: 0)", file=sys.stderr)
            print("  num_mutations: Number of mutations per corpus item (default: 100)", file=sys.stderr)
            sys.exit(1)
    else:
        # Default: test with seeds 0-99 (100 mutations per base)
        seeds = list(range(100))
        num_mutations = len(seeds)

    print("=" * 70)
    print("ASTON Mutation-Based Fuzz Testing")
    print("=" * 70)
    print(f"Base corpus: {len(BASE_CORPUS)} samples")
    print(f"Mutations per sample: {num_mutations}")
    print(f"Total tests: {len(BASE_CORPUS) * num_mutations}")
    print()

    total_tests = 0
    passed = 0
    failed = 0
    failures = []

    # Test mutations of each corpus item
    for base_idx, base_code in enumerate(BASE_CORPUS):
        print(f"[{base_idx+1}/{len(BASE_CORPUS)}] Testing base: {base_code[:50]}...")

        base_passed = 0
        base_failed = 0

        for seed in seeds:
            total_tests += 1
            mutation_id = f"base{base_idx}_seed{seed}"

            success, error, mutated_code = test_mutation(base_code, seed, mutation_id)

            if success:
                passed += 1
                base_passed += 1
            else:
                failed += 1
                base_failed += 1

                # Save failure
                filepath = save_failure(mutated_code, seed, base_idx)

                failures.append({
                    'base_idx': base_idx,
                    'seed': seed,
                    'filepath': filepath,
                    'error': error,
                    'base_code': base_code,
                })

                print(f"  ✗ Mutation seed={seed} FAILED")
                print(f"    Saved to: {filepath}")
                print(f"    Error: {error[:100]}")
                print(f"    Reproduce: python3 test_aston_fuzz_mutations.py {seed} 1")

        if base_failed == 0:
            print(f"  ✓ All {base_passed} mutations passed")
        else:
            print(f"  ⚠ {base_passed} passed, {base_failed} failed")

    # Summary
    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)
    print(f"Total tests:  {total_tests}")
    print(f"Passed:       {passed} ({100*passed//total_tests if total_tests > 0 else 0}%)")
    print(f"Failed:       {failed}")

    if failures:
        print("\n" + "=" * 70)
        print("Failures")
        print("=" * 70)
        for f in failures:
            print(f"\nBase {f['base_idx']}: {f['base_code'][:50]}")
            print(f"  Seed: {f['seed']}")
            print(f"  File: {f['filepath']}")
            print(f"  Reproduce: python3 test_aston_fuzz_mutations.py {f['seed']} 1")
            print(f"  Test file: python3 aston.py --test {f['filepath']}")

    if failed > 0:
        print("\n✗ MUTATION FUZZ TEST FAILED")
        sys.exit(1)
    else:
        print("\n✓ ALL MUTATION FUZZ TESTS PASSED")
        sys.exit(0)


if __name__ == '__main__':
    main()
