"""
Tests for async/await function support.

Tests that async functions are normalized correctly and maintain hash determinism.
"""
import ast
from unittest.mock import patch

import pytest

import ouverture
from tests.conftest import normalize_code_for_test


def test_normalize_simple_async_function():
    """Test normalizing a simple async function"""
    code = '''async def fetch_data():
    """Fetch data asynchronously"""
    return await some_api()
'''
    tree = ast.parse(code)

    # Extract function - should work with async
    func_def, imports = ouverture.function_extract_definition(tree)

    assert isinstance(func_def, ast.AsyncFunctionDef)
    assert func_def.name == "fetch_data"


def test_normalize_async_function_with_parameters():
    """Test normalizing async function with parameters"""
    code = '''async def process_item(item, timeout):
    """Process an item with timeout"""
    result = await do_work(item)
    return result
'''
    tree = ast.parse(code)
    func_def, imports = ouverture.function_extract_definition(tree)

    # Create name mapping
    name_mapping, reverse_mapping = ouverture.mapping_create_name(func_def, imports, {})

    # Function name should be _ouverture_v_0
    assert name_mapping["process_item"] == "_ouverture_v_0"
    # Parameters should be mapped
    assert "item" in name_mapping
    assert "timeout" in name_mapping
    # Local variable should be mapped
    assert "result" in name_mapping


def test_normalize_async_function_with_await_expressions():
    """Test normalizing async function with multiple await expressions"""
    code = '''async def complex_async(url, data):
    """Complex async operation"""
    connection = await connect(url)
    response = await connection.send(data)
    result = await response.json()
    return result
'''
    tree = ast.parse(code)
    func_def, imports = ouverture.function_extract_definition(tree)

    # Should extract all local variables
    name_mapping, reverse_mapping = ouverture.mapping_create_name(func_def, imports, {})

    # All identifiers should be mapped
    assert "_ouverture_v_0" in reverse_mapping  # function name
    assert "url" in name_mapping
    assert "data" in name_mapping
    assert "connection" in name_mapping
    assert "response" in name_mapping
    assert "result" in name_mapping


def test_async_function_hash_determinism():
    """Test that same async logic produces same hash"""
    # English version
    code_eng = '''async def fetch_user(user_id):
    """Fetch user by ID"""
    result = await get_from_db(user_id)
    return result
'''

    # Same logic, different docstring (simulating French)
    code_fra = '''async def fetch_user(user_id):
    """Récupérer utilisateur par ID"""
    result = await get_from_db(user_id)
    return result
'''

    tree_eng = ast.parse(code_eng)
    tree_fra = ast.parse(code_fra)

    # Normalize both - use the WITHOUT docstring version (second return value) for hashing
    _, normalized_eng_no_doc, docstring_eng, name_map_eng, alias_map_eng = ouverture.ast_normalize(tree_eng, "eng")
    _, normalized_fra_no_doc, docstring_fra, name_map_fra, alias_map_fra = ouverture.ast_normalize(tree_fra, "fra")

    # Compute hashes from code WITHOUT docstring (as per design)
    hash_eng = ouverture.hash_compute(normalized_eng_no_doc)
    hash_fra = ouverture.hash_compute(normalized_fra_no_doc)

    # Hashes should be identical (logic is same, docstring excluded from hash)
    assert hash_eng == hash_fra


def test_async_function_preserves_async_keyword():
    """Test that normalized code preserves async keyword"""
    code = '''async def my_async_func():
    """Do async stuff"""
    return await something()
'''
    tree = ast.parse(code)

    normalized_with_doc, normalized_without_doc, docstring, name_mapping, alias_mapping = ouverture.ast_normalize(tree, "eng")

    # The normalized code should still have async
    assert "async def _ouverture_v_0" in normalized_with_doc
    assert "async def _ouverture_v_0" in normalized_without_doc


def test_ast_normalizer_visit_async_function_def():
    """Test ASTNormalizer handles AsyncFunctionDef"""
    code = '''async def original_name():
    pass
'''
    tree = ast.parse(code)

    name_mapping = {"original_name": "_ouverture_v_0"}
    normalizer = ouverture.ASTNormalizer(name_mapping)
    transformed = normalizer.visit(tree)

    # Function should be renamed
    func_def = transformed.body[0]
    assert isinstance(func_def, ast.AsyncFunctionDef)
    assert func_def.name == "_ouverture_v_0"


def test_names_collect_includes_async_function():
    """Test names_collect handles async functions"""
    code = '''async def async_func(param):
    local_var = 42
    return local_var
'''
    tree = ast.parse(code)

    # Collect names (API takes only tree argument)
    names = ouverture.names_collect(tree)

    assert "async_func" in names
    assert "param" in names
    assert "local_var" in names


def test_async_function_add_and_get(mock_ouverture_dir):
    """Integration test: Add async function, then retrieve it"""
    test_file = mock_ouverture_dir / "async_test.py"
    original_code = '''async def fetch_data(endpoint):
    """Fetch data from endpoint"""
    response = await make_request(endpoint)
    return response
'''
    test_file.write_text(original_code, encoding='utf-8')

    # Add function
    hash_value = None
    with patch('builtins.print') as mock_print:
        ouverture.function_add(f"{test_file}@eng")
        for call in mock_print.call_args_list:
            args = str(call)
            if 'Hash:' in args:
                hash_value = args.split('Hash: ')[1].split("'")[0]

    assert hash_value is not None

    # Get function back
    output = []
    with patch('builtins.print', side_effect=lambda x: output.append(x)):
        ouverture.function_get(f"{hash_value}@eng")

    retrieved_code = '\n'.join(output)

    # Should contain async keyword and original names
    assert "async def fetch_data" in retrieved_code
    assert "endpoint" in retrieved_code
    assert "response" in retrieved_code


def test_async_multilingual_same_hash(mock_ouverture_dir):
    """Integration test: Same async logic in multiple languages produces same hash"""
    # English version
    eng_file = mock_ouverture_dir / "english_async.py"
    eng_file.write_text('''async def download_file(url, destination):
    """Download a file from URL to destination"""
    data = await fetch(url)
    await save(data, destination)
    return True
''', encoding='utf-8')

    # French version (same logic, French docstring)
    fra_file = mock_ouverture_dir / "french_async.py"
    fra_file.write_text('''async def download_file(url, destination):
    """Télécharger un fichier depuis URL vers destination"""
    data = await fetch(url)
    await save(data, destination)
    return True
''', encoding='utf-8')

    # Add both
    eng_hash = None
    fra_hash = None

    with patch('builtins.print') as mock_print:
        ouverture.function_add(f"{eng_file}@eng")
        for call in mock_print.call_args_list:
            args = str(call)
            if 'Hash:' in args:
                eng_hash = args.split('Hash: ')[1].split("'")[0]

    with patch('builtins.print') as mock_print:
        ouverture.function_add(f"{fra_file}@fra")
        for call in mock_print.call_args_list:
            args = str(call)
            if 'Hash:' in args:
                fra_hash = args.split('Hash: ')[1].split("'")[0]

    # Should have the same hash
    assert eng_hash == fra_hash

    # Should be able to retrieve in both languages
    with patch('builtins.print'):
        ouverture.function_get(f"{eng_hash}@eng")
        ouverture.function_get(f"{fra_hash}@fra")


def test_async_function_show(mock_ouverture_dir):
    """Test show command works with async functions"""
    test_file = mock_ouverture_dir / "async_show.py"
    test_file.write_text('''async def greet_async(name):
    """Greet someone asynchronously"""
    await prepare()
    return f"Hello, {name}!"
''', encoding='utf-8')

    # Add function
    hash_value = None
    with patch('builtins.print') as mock_print:
        ouverture.function_add(f"{test_file}@eng")
        for call in mock_print.call_args_list:
            args = str(call)
            if 'Hash:' in args:
                hash_value = args.split('Hash: ')[1].split("'")[0]

    assert hash_value is not None

    # Show function
    output = []
    def capture_print(x='', **kwargs):
        output.append(str(x))

    with patch('builtins.print', side_effect=capture_print):
        ouverture.function_show(f"{hash_value}@eng")

    output_text = '\n'.join(output)

    # Should contain async function
    assert 'async def greet_async' in output_text
    assert 'name' in output_text
    assert 'Hello' in output_text
