# 使用有向无环图(DAG)优化ObjChain生成的代码，减少中间变量的数量
from pyobject.objproxy.utils import *

MERGABLE_INFO = ["_alias_name"]

class Statement: # 图节点（一条语句）
    def __init__(self,graph,code,var,dependency_vars,extra_info=None):
        self.graph = graph
        self.code = code
        self.var = var
        self.extra_info = extra_info or {}
        self.removed = False
        self.depends = set()
        self.affects = set() # 在update_affects中初始化
        self.affects_cnt = 0 # 使用affect_cnt替代len(self.affects)，是由于变量可能重复出现，如func(var1, var1 ** 2)
        for var in dependency_vars:
            self.depends.add(graph.get_node(var))
    def optimize_self(self, remove_internal=True, remove_export_type=True): # 如果自身是临时或未使用变量，则优化自身
        if not self.var or self.var in self.graph.no_optimize_vars:
            return
        # 只有一个影响语句时，将自身的值代入，否则直接删除自身
        if self.affects_cnt == 1:
            for affect in self.affects:
                try:
                    affect.code = subst_var(affect.code, self.code) # 代入变量
                except NotAssignmentError:return # 不是赋值语句（如import numpy as np）
                affect.depends.remove(self)
                affect.depends |= self.depends # 将自身的依赖合并到影响语句的依赖
                self.merge_info_into(affect) # 合并自身的可合并信息
            for dep in self.depends:
                dep.affects.remove(self)
                dep.affects |= self.affects
                dep.affects_cnt += self.affects_cnt - 1 # 更新计数
            #self.graph._remove_statement(self) # 不使用
            self.removed = True # 标记自身将被移除（不是真正删除）
        elif self.affects_cnt == 0: # 自身不影响任何其他语句
            try:
                self.code = trim_assign(self.code)
                self.var = None
            except NotAssignmentError:pass # 不是赋值语句
            if remove_internal and self.extra_info.get("_internal",False)\
               or remove_export_type and self.extra_info.get("_export_type",False):
                for dep in self.depends:
                    dep.affects.remove(self)
                    dep.affects_cnt -= 1
                self.removed = True
    def merge_info_into(self, stat, mergable=None): # 将自身的extra_info信息合并到stat
        if mergable is None:mergable = MERGABLE_INFO
        for key in self.extra_info:
            if key not in mergable:continue
            stat.extra_info[key] = self.extra_info[key]
    def __str__(self):
        return f"""<Statement `{self.code}` var={self.var!r} \
depends={[dep.var for dep in self.depends]} \
affects={[affect.var or ReprWrapper('<stat>') for affect in self.affects]} \
(cnt:{self.affects_cnt}) extra_info={self.extra_info}\
{' removed=True' if self.removed else ''}>"""
    __repr__ = __str__

class VarGraph:
    def __init__(self,codes,code_vars,no_optimize_vars=None):
        self.vars={}
        self.statements=[]
        self.no_optimize_vars = no_optimize_vars if no_optimize_vars \
                                is not None else [] # 不优化的变量
        for code, code_var in zip(codes,code_vars):
            statement = Statement(self,code,*code_var)
            self.statements.append(statement)
            if code_var[0] is not None:
                self.vars[code_var[0]] = statement
        self.update_affects()
    def get_node(self,name):
        return self.vars[name]
    def update_affects(self): # 更新每个节点的影响的语句
        for stat in self.statements:
            for depend in stat.depends:
                depend.affects.add(stat)
                depend.affects_cnt += 1

    def _remove_statement(self,stat): # 直接从statements列表移除语句
        assert stat.graph is self
        self.statements.remove(stat)
        if stat.var is not None:
            del self.vars[stat.var]
    def clear_removed_statements(self): # 清除暂时保留的removed设为True的语句（由于遍历过程中statements长度不可变）
        for stat in self.statements.copy():
            if stat.removed:
                self._remove_statement(stat)

    def optimize(self, remove_internal=True, remove_export_type=True): # 优化代码，可多次调用
        for stat in self.statements:
            stat.optimize_self(remove_internal,remove_export_type)
        self.clear_removed_statements()
    def get_code(self):
        return "\n".join(stat.code for stat in self.statements if not stat.removed)

def import_optimizer(graph):
    # 将__import__函数调用改为import语句，并去掉无用的__import__，就地修改graph
    for stat in graph.statements:
        try:
            stat.code = optimize_import(stat.code)
        except NotAnImportError:pass
        
    graph.clear_removed_statements()

def import_alias_optimizer(graph):
    for stat in graph.statements:
        if stat.extra_info.get("_alias_name") is not None: # 重命名模块别名
            pre_var = stat.var
            stat.var = stat.extra_info["_alias_name"]
            stat.code = rename_var(stat.code, {pre_var: stat.var})
            for affect in stat.affects:
                affect.code = rename_var(affect.code, {pre_var: stat.var})
                if pre_var in graph.vars:
                    del graph.vars[pre_var]
                graph.vars[stat.var] = stat

def unused_import_optimizer(graph):
    for stat in graph.statements:
        if is_unused_import(stat.code):
            stat.remove = True # 标记为将被移除
    graph.clear_removed_statements()

def optimize_code(codes, code_vars, no_optimize_vars=None,
                  remove_internal=True, remove_export_type=True,
                  optimize_imports=True):
    # no_optimize_vars: 不能移除的变量名的列表
    # remove_internal: 移除执行代码本身时产生的内部代码
    # remove_export_type: 移除无用的类型导出，如str(var)
    graph = VarGraph(codes,code_vars,no_optimize_vars)
    statement_cnt = len(graph.statements)
    if optimize_imports:
        import_optimizer(graph) # 避免__import__()的调用本身在后续被优化
    while True:
        graph.optimize(remove_internal,remove_export_type)
        #from pprint import pprint;pprint(graph.statements);print()
        if statement_cnt == len(graph.statements):
            break
        statement_cnt = len(graph.statements)
    if optimize_imports:
        import_alias_optimizer(graph)
        import_optimizer(graph)
        unused_import_optimizer(graph)
    return graph.get_code()

def test():
    raw = """\
submod = __import__("module.sub.submod").sub.submod
temp_var = [1,2,3]
unused_var = submod.func(temp_var)"""
    print("\nRaw:\n", raw, sep="")
    print("\nOptimized:\n",optimize_code(raw.splitlines(),
            [("submod",[]),("temp_var",[]),
             ("unused_var",["submod","temp_var"])]), sep="")

if __name__=="__main__":test()