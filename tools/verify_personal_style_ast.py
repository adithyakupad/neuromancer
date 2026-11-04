"""Verify only the declared readability transformations against Git source."""
import ast
import hashlib
import json
import subprocess
from pathlib import Path


class Normalize(ast.NodeTransformer):
    def __init__(self, filename, candidate):
        self.filename = filename
        self.candidate = candidate
        self.changes = []

    def visit_FunctionDef(self, node):
        if (self.candidate and self.filename == "identify.py"
                and node.name == "forecast"):
            renames = {"rate_history": "ys", "current_history": "us",
                       "predictions": "pred", "predicted_rate": "value",
                       "feature_row": "x"}
            for child in ast.walk(node):
                if isinstance(child, ast.Name) and child.id in renames:
                    child.id = renames[child.id]
            self.changes.append("forecast local names")
        if (self.candidate and self.filename == "control.py"
                and node.name == "accept"):
            for child in ast.walk(node):
                if isinstance(child, ast.Name) and child.id == "proposed_integral":
                    child.id = "proposed"
            self.changes.append("integral proposal local name")
        result = self.generic_visit(node)
        self.remove_docstring(result)
        return result

    def visit_ClassDef(self, node):
        result = self.generic_visit(node)
        self.remove_docstring(result)
        return result

    def visit_Module(self, node):
        result = self.generic_visit(node)
        self.remove_docstring(result)
        return result

    @staticmethod
    def remove_docstring(node):
        if (node.body and isinstance(node.body[0], ast.Expr)
                and isinstance(node.body[0].value, ast.Constant)
                and isinstance(node.body[0].value.value, str)):
            node.body = node.body[1:]

    def visit_If(self, node):
        if self.candidate and self.filename == "control.py":
            expected = ast.parse('''if name == "ZERO":
    self.q = 0.0
elif name == "MAX":
    self.q = 120.0
else:
    self.q = calibration.feedforward_pA
''').body[0]
            if ast.dump(node) == ast.dump(expected):
                self.changes.append("explicit policy initialization branches")
                return ast.parse('self.q = 0.0 if name == "ZERO" else 120.0 if name == "MAX" else calibration.feedforward_pA').body[0]
        if self.candidate and self.filename in ("predictive.py", "online_identify.py"):
            for index, statement in enumerate(node.body[:-1]):
                expected = ast.parse("residual = v - z @ self.theta").body[0]
                if ast.dump(statement) == ast.dump(expected):
                    following = node.body[index + 1]
                    expected_next = ast.parse("theta = self.theta + np.outer(gain, residual)").body[0]
                    assert ast.dump(following) == ast.dump(expected_next)
                    node.body[index + 1] = ast.parse("theta = self.theta + np.outer(gain, v - z @ self.theta)").body[0]
                    del node.body[index]
                    self.changes.append("named old-state RLS residual")
                    break
        return self.generic_visit(node)


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference_revision")
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    results = {}
    for name in ("identify.py", "online_identify.py", "control.py", "predictive.py"):
        original = subprocess.check_output(["git", "show", f"{args.reference_revision}:src/neuromancer/{name}"])
        candidate = (args.source / name).read_bytes()
        old_normalizer = Normalize(name, False)
        new_normalizer = Normalize(name, True)
        old_tree = old_normalizer.visit(ast.parse(original))
        new_tree = new_normalizer.visit(ast.parse(candidate))
        assert ast.dump(old_tree) == ast.dump(new_tree), name
        results[name] = dict(original_sha256=hashlib.sha256(original).hexdigest(),
                             candidate_sha256=hashlib.sha256(candidate).hexdigest(),
                             normalized_ast_equal=True, declared_changes=new_normalizer.changes)
    args.output.write_text(json.dumps(results, indent=2) + "\n")
    print("PASS: only declared readability transformations")


if __name__ == "__main__":
    main()
