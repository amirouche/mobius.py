# LIMITS

## Potential Enhancements

1. **Class support**: Would require normalizing method names, class hierarchy, etc.
2. **Multiple functions per file**: Would require dependency tracking within the file
3. **Async function support**: Add `ast.AsyncFunctionDef` handling
4. **Semantic equivalence**: Detect functionally equivalent but syntactically different code
5. **Type hint normalization**: Optionally normalize type hints for consistent hashing
6. **Import validation**: Verify mobius imports exist in the pool
7. **Cross-language support**: Extend beyond Python (JavaScript, Rust, etc.)
8. **Version migration**: Handle schema changes in stored JSON format

## Research Questions

1. **Composability**: How deep can function composition go before performance degrades?
2. **Cognitive impact**: Does coding in native language improve comprehension and reduce bugs?
3. **LLM training**: Could multilingual function pools improve LLM performance on non-English code?
4. **Scale**: How large can the function pool grow before search/retrieval becomes slow?
