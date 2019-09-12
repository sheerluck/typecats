"""A Plugin for MyPy that helps it understand the Cats wrapper around attrs and cattrs"""
# flake8: noqa
# pylint: skip-file
# pylint: disable=import-error
import typing as ty
from mypy.nodes import (
    Var,
    Argument,
    ARG_POS,
    FuncDef,
    PassStmt,
    Block,
    SymbolTableNode,
    MDEF,
    SymbolTable,
    TypeInfo,
)
from mypy.types import NoneTyp, Type, CallableType, AnyType
from mypy.typevars import fill_typevars
from mypy.semanal import set_callable_name
from mypy.plugin import Plugin, ClassDefContext
from mypy.plugins.attrs import attr_class_maker_callback
from mypy.plugins.common import add_method


CAT_PATH = "typecats.tc.Cat"
STRUCTURE_NAME = "struc"
TRY_STRUCTURE_NAME = "try_struc"
UNSTRUCTURE_NAME = "unstruc"


def plugin(_version: str):
    """Plugin for MyPy Typechecking of Cats"""
    return CatsPlugin


class CatsPlugin(Plugin):
    """A plugin to make MyPy understand Cats"""

    def get_class_decorator_hook(
        self, fullname: str
    ) -> ty.Optional[ty.Callable[[ClassDefContext], None]]:
        """One of the MyPy Plugin defined entry points"""

        def add_struc_and_unstruc_to_classdefcontext(cls_def_ctx):
            """This MyPy hook tells MyPy that struc and unstruc will be present on a Cat"""

            dict_type = cls_def_ctx.api.named_type("__builtins__.dict")
            str_type = cls_def_ctx.api.named_type("__builtins__.str")

            if fullname == CAT_PATH:
                attr_class_maker_callback(
                    cls_def_ctx, True
                )  # since a Cat is also an attr.s class...
                info = cls_def_ctx.cls.info

                if STRUCTURE_NAME not in info.names:
                    add_static_method(
                        cls_def_ctx,
                        STRUCTURE_NAME,
                        [Argument(Var("d", dict_type), dict_type, None, ARG_POS)],
                        fill_typevars(info),
                    )
                if TRY_STRUCTURE_NAME not in info.names:
                    # print('adding ' + TRY_STRUCTURE_NAME + ' to ' + str(info.fullname()) )
                    add_static_method(
                        cls_def_ctx,
                        TRY_STRUCTURE_NAME,
                        [Argument(Var("d", dict_type), dict_type, None, ARG_POS)],
                        fill_typevars(info),
                    )
                if UNSTRUCTURE_NAME not in info.names:
                    add_method(cls_def_ctx, UNSTRUCTURE_NAME, [], dict_type)

        if fullname == CAT_PATH:
            return add_struc_and_unstruc_to_classdefcontext
        return None


def serialize_info_name(
    info: TypeInfo, name: str, class_path: str
) -> ty.Dict[str, ty.Any]:
    slzed = info.names[name].serialize(class_path, name)
    return slzed


def deserialize_funcdefs(stmts):
    return [FuncDef.deserialize(stmt) for stmt in stmts if stmt[".class"] == "FuncDef"]


def add_static_method(
    ctx, name: str, args: ty.List[Argument], return_type: Type
) -> None:
    """Mostly copied from mypy.plugins.common, with changes to make it work for a static method."""
    info = ctx.cls.info
    function_type = ctx.api.named_type("__builtins__.function")

    arg_types, arg_names, arg_kinds = [], [], []
    for arg in args:
        assert arg.type_annotation, "All arguments must be fully typed."
        arg_types.append(arg.type_annotation)
        arg_names.append(arg.variable.name())
        arg_kinds.append(arg.kind)

    signature = CallableType(
        arg_types, arg_kinds, arg_names, return_type, function_type
    )

    func = FuncDef(name, args, Block([PassStmt()]))
    func.is_static = True
    func.info = info
    func.type = set_callable_name(signature, func)
    func._fullname = info.fullname() + "." + name
    func.line = info.line

    info.names[name] = SymbolTableNode(MDEF, func, plugin_generated=True)
    info.defn.defs.body.append(func)
