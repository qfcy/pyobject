# 代码生成和优化的辅助函数
import ast
if not hasattr(ast,"unparse"): # Python 3.8及以下版本
    from astor import to_source
else:
    to_source = ast.unparse # pylint: disable=no-member

__all__ = ["format_func_call","NotAssignmentError","NotAnImportError",
           "subst_var","rename_var","trim_assign","is_unused_import",
           "optimize_import","ReprWrapper"]

class ReprWrapper:
    def __init__(self,_repr):
        self._repr = _repr
    def __repr__(self):
        return self._repr
    __str__ = __repr__

def format_func_call(args,kw,repr_=None): # 格式化函数调用的代码
    if repr_ is None:repr_=repr
    return "{}{}{}".format(", ".join(repr_(elem) for elem in args),
            ", " if args and kw else "", # 中间的分隔逗号
            ", ".join("{}={}".format(k,repr_(v)) for k,v in kw.items()))

class NotAssignmentError(ValueError):pass
class NotAnImportError(ValueError):pass

class ReplaceVarVisitor(ast.NodeTransformer):
    def __init__(self, replacements):
        self.replacements = replacements

    def visit_Name(self, node):
        if node.id in self.replacements:
            # 使用 ast.parse 解析替换表达式
            replacement_ast = self.replacements[node.id]
            return replacement_ast
        return node

def subst_var(source, *assign_statements):
    # 代入变量的值，如replace_var("y=f(x)","x=1")返回"y=f(1)"
    replacements = {}
    for assign in assign_statements:
        body = ast.parse(assign, mode='exec').body
        node = body[0] if len(body) == 1 else None
        if node is None or not isinstance(node, ast.Assign):
            raise NotAssignmentError(f"{assign} should be an assign statement")
        value = node.value
        for target in node.targets:
            replacements[target.id] = value

    tree = ast.parse(source)
    new_tree = ReplaceVarVisitor(replacements).visit(tree)
    return to_source(new_tree).strip()

def rename_var(source, varname_mapping):
    # varname_mapping: 变量名的映射，如{"x":"y"}表示变量名x被替换成y
    stats = []
    for from_,to in varname_mapping.items():
        stats.append(f"{from_} = {to}")
    return subst_var(source, *stats)

def trim_assign(source):
    # 去除赋值语句中的变量赋值，如trim_varname("y=f(x)")返回"f(x)"
    body = ast.parse(source, mode='exec').body
    if not body: # 空语句，如注释
        return source

    node = body[0]
    if len(body) > 1 or not isinstance(node, ast.Assign):
        raise NotAssignmentError(f"{source} should be an assign statement")
    return to_source(node.value).strip()

def is_unused_import(source): # 是否为孤立的调用__import__的语句
    tree = ast.parse(source)
    if not isinstance(tree, ast.Call) \
            or not isinstance(tree.func, ast.Name) \
            or tree.func.id != "__import__":
        return False
    return True

def optimize_import(source):
    # 优化__import__语句，如plt=__import__('matplotlib.pyplot').pyplot优化成import matplotlib.pyplot as plt
    body = ast.parse(source).body
    if not body:return source # 空语句，如注释
    assign_node = body[0]
    if not isinstance(body[0], ast.Assign):
        raise NotAnImportError("Input must be an assignment statement with __import__")

    import_call = assign_node.value
    while isinstance(import_call, ast.Attribute): # 跳过属性部分
        import_call = import_call.value

    if not isinstance(import_call, ast.Call) \
            or not isinstance(import_call.func, ast.Name) \
            or import_call.func.id != "__import__":
        raise NotAnImportError("Input must be a __import__ call")

    module_name = import_call.args[0].s  # 模块路径字符串
    attribute_chain = []
    node = assign_node.value
    while isinstance(node, ast.Attribute):
        attribute_chain.append(node.attr)
        node = node.value
    attribute_chain.reverse()

    submod_chain = module_name.split(".")[1:]
    if submod_chain != attribute_chain:
        return source # 属性访问和模块名称不一致，返回原始语句

    # 构建导入语句
    alias = assign_node.targets[0].id
    return f"import {module_name} as {alias}"
