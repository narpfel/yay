import ast
import sys
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path

import yay


def import_yay_file(yay_filename, name="main"):
    spec = spec_for_yay_file(yay_filename, name)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def spec_for_yay_file(yay_filename, module_name="main"):
    loader = YayFileLoader(module_name, yay_filename)
    return spec_from_loader(loader.name, loader)


class YayFinder:
    def find_on_path(self, name):
        parts = name.split(".")
        for path in map(Path, sys.path):
            filename = path.joinpath(*parts).with_suffix(".yay")
            if filename.exists():
                return str(filename)

    def find_spec(self, name, path, target=None):
        if target is not None:
            raise ImportError("`target is not None` case is not supported")

        filename = self.find_on_path(name)
        if filename is not None:
            return spec_for_yay_file(filename, name)


class YayFileLoader(SourceFileLoader):
    def source_to_code(self, data, *args, **kwargs):
        node = yay.ast.parse(data)
        node = MovTransformer().visit(node)
        node = ToPythonAstTransformer().visit(node)
        ast.fix_missing_locations(node)
        return super().source_to_code(
            node,
            *args,
            **kwargs
        )


class CopyLocationMixin:
    def visit(self, node):
        return yay.ast.copy_location(
            super().visit(node),
            node
        )


class MovTransformer(CopyLocationMixin, yay.ast.NodeTransformer):
    def visit_ArrowAssign(self, node):
        if len(node.targets) > 1:
            raise RuntimeError("This cannot happen!")

        return yay.ast.Expr(
            yay.ast.Call(
                func=yay.ast.Name(id="mov", ctx=yay.ast.Load()),
                args=[node.targets[0], node.value],
                keywords=[]
            )
        )


class ToPythonAstTransformer(CopyLocationMixin, yay.ast.NodeTransformer):
    def replace_node(self, node):
        self.generic_visit(node)

        PyAstType = getattr(ast, type(node).__name__)
        return PyAstType(**dict(yay.ast.iter_fields(node)))

    def __getattr__(self, name):
        if not name.startswith("visit_"):
            raise AttributeError
        return self.replace_node
