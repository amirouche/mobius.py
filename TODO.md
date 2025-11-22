# TODO

<!-- Format: bullet list with topic, type names, intended feature - one sentence max -->
<!-- Remove implemented entries in atomic commits (separate from feature commits) -->

- `pipe`: command to read stdin, apply function, write result to stdout
- `edit`: command to open function in $EDITOR, save as new hash on exit
- `cat`: command to output raw normalized code to stdout (no denormalization)
- `add`: support stdin input with `-` placeholder (e.g., `echo "def f(x): return x+1" | mobius.py add -@eng`)
- `diff`: command to diff two functions by hash
- `git`: command to generate commit message from pool changes
- `comment`: command to add/view comments on a function hash
- `html`: command to render pool as static HTML site for browsing
- `compile`: test, QA, and bulletproof build process and dependency bundling
- `run`: thoroughly review including --debug and arguments passing (no implicit coercion)
- `log`: thoroughly review output formatting and metadata display
- `search`: thoroughly review query parsing and result ranking
- `compile`: thoroughly review build process and dependency bundling
- `compile`: add --python flag to produce a single Python file
- `compile`: drop --output flag, use a.out or a.out.exe as default output
- `review`: make interactive, request explicit ack for security/correctness, one function at a time starting from lowest level, remember reviewed functions
- `validate`: validate whole mobius directory including pool and config
