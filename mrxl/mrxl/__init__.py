from .parse import parse
from . import ast
import sys
import json


class InterpError(Exception):
    pass


def _dict_zip(d):
    """Given a dict of lists, generate a sequence of dicts with the same
    keys---each associated with one "slice" of the lists.
    """
    for i in range(len(next(iter(d.values())))):
        yield {k: v[i] for k, v in d.items()}


def interp_expr(expr: ast.Expr, env):
    if isinstance(expr, ast.LitExpr):
        return expr.value
    elif isinstance(expr, ast.VarExpr):
        return env[expr.name]
    elif isinstance(expr, ast.BinExpr):
        lhs = interp_expr(expr.lhs, env)
        rhs = interp_expr(expr.rhs, env)
        if expr.op == "add":
            return lhs + rhs
        elif expr.op == "mul":
            return lhs * rhs
        elif expr.op == "sub":
            return lhs - rhs
        elif expr.op == "div":
            return lhs / rhs
        else:
            raise InterpError(f"unhandled binary operator: {expr.op}")
    else:
        raise InterpError(f"unhandled expression: {type(expr)}")


def interp(prog: ast.Prog, data):
    env = {}

    # Load input data into environment.
    for decl in prog.decls:
        if decl.input:
            try:
                env[decl.name] = data[decl.name]
            except KeyError:
                raise InterpError(f"input data for `{decl.name}` not found")

    for stmt in prog.stmts:
        if isinstance(stmt.op, ast.Map):
            bind_data = {}
            for bind in stmt.op.bind:
                if len(bind.dest) != 1:
                    raise InterpError("map binds are unary")
                try:
                    bind_data[bind.dest[0]] = env[bind.src]
                except KeyError:
                    raise InterpError(f"source `{bind.src}` for map not found")

            # Compute the map.
            env[stmt.dest] = [
                interp_expr(stmt.op.body, env)
                for env in _dict_zip(bind_data)
            ]

        elif isinstance(stmt.op, ast.Reduce):
            raise InterpError("reduce unsupported")

        else:
            raise InterpError(f"unknown op {type(stmt.op)}")

    # Emit the output values.
    out = {}
    for decl in prog.decls:
        if not decl.input:
            try:
                out[decl.name] = env[decl.name]
            except KeyError:
                raise InterpError(f"output value `{decl.name}` not found")
    return out


def main():
    with open(sys.argv[1]) as f:
        txt = f.read()
    with open(sys.argv[2]) as f:
        data = json.load(f)
    ast = parse(txt)

    try:
        out = interp(ast, data)
    except InterpError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)

    print(json.dumps(out, sort_keys=True, indent=2))


if __name__ == '__main__':
    main()
