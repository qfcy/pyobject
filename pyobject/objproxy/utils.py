import ast
if not hasattr(ast,"unparse"):
    from astor import to_source
else:
    to_source = ast.unparse # pylint: disable=no-member

class _ReprWrapper:
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

class NotAssignmentError(ValueError):
    pass

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
        node = body[0] if body else None
        if node is None or not isinstance(node, ast.Assign):
            raise NotAssignmentError(f"{assign} should be an assign statement")
        value = node.value
        for target in node.targets:
            replacements[target.id] = value

    tree = ast.parse(source)
    new_tree = ReplaceVarVisitor(replacements).visit(tree)
    return to_source(new_tree).strip()

def trim_assign(source):
    # 去除赋值语句中的变量赋值，如trim_varname("y=f(x)")返回"f(x)"
    node = ast.parse(source, mode='exec').body[0]
    if not isinstance(node, ast.Assign):
        raise NotAssignmentError(f"{source} should be an assign statement")
    return to_source(node.value).strip()