"""Record readability metrics and AST identity relative to the integrated baseline."""
import ast
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tokenize


def inspect(source):
    tree = ast.parse(source)
    tokens = tokenize.generate_tokens(io.StringIO(source).readline)
    decisions = (ast.If, ast.IfExp, ast.For, ast.While, ast.Try, ast.BoolOp, ast.Match)
    functions = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            branches = sum(isinstance(child, decisions) for child in ast.walk(node))
            functions.append((branches, node.end_lineno - node.lineno + 1, node.name))
    return dict(max_line=max(map(len, source.splitlines()), default=0),
                semicolons=sum(token.type == tokenize.OP and token.string == ";" for token in tokens),
                long_lines=sum(len(line) > 100 for line in source.splitlines()),
                largest_functions=sorted(functions, reverse=True)[:3],
                source_sha256=hashlib.sha256(source.encode()).hexdigest(),
                ast_sha256=hashlib.sha256(ast.dump(tree).encode()).hexdigest())


def main(baseline, output):
    tracked = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", baseline], text=True)
    files = [Path(name) for name in tracked.splitlines()
             if name.endswith(".py") and name.startswith(("src/neuromancer/", "scripts/", "tests/"))]
    results = {}
    for path in files:
        previous = subprocess.check_output(["git", "show", f"{baseline}:{path}"]).decode()
        current = path.read_text()
        results[str(path)] = dict(before=inspect(previous), after=inspect(current))
    output.write_text(json.dumps(results, indent=2) + "\n")


if __name__ == "__main__":
    main(sys.argv[1], Path(sys.argv[2]))
