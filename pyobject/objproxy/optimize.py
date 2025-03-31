# 使用有向无环图(DAG)优化ObjChain生成的代码，减少中间变量的数量
from pyobject.objproxy.utils import subst_var, trim_assign, \
                                    NotAssignmentError, _ReprWrapper

class Statement: # 图节点（一条语句）
    def __init__(self,graph,code,var,dependency_vars,extra_info):
        self.graph = graph
        self.code = code
        self.var = var
        self.extra_info = extra_info
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
            for dep in self.depends:
                dep.affects.remove(self)
                dep.affects |= self.affects
                dep.affects_cnt += self.affects_cnt - 1 # 更新计数
            #self.graph.remove_statement(self)
            self.removed = True # 标记自身已被移除（不是真正删除）
        elif self.affects_cnt == 0:
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

    def __str__(self):
        return f"""<Statement `{self.code}` var={self.var!r} \
depends={[dep.var for dep in self.depends]} \
affects={[affect.var or _ReprWrapper('<stat>') for affect in self.affects]} \
(cnt:{self.affects_cnt})>"""
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

    def remove_statement(self,stat):
        assert stat.graph is self
        self.statements.remove(stat)
        if stat.var is not None:
            del self.vars[stat.var]
    def clear_removed_statements(self): # 清除暂时保留的已删除语句（由于遍历过程中statements长度不可变）
        for stat in self.statements.copy():
            if stat.removed:
                self.remove_statement(stat)

    def optimize(self, remove_internal=True, remove_export_type=True): # 优化代码，可多次调用
        for stat in self.statements:
            stat.optimize_self(remove_internal,remove_export_type)
        self.clear_removed_statements()
    def get_code(self):
        return "\n".join(stat.code for stat in self.statements if not stat.removed)

def optimize_code(codes, code_vars, no_optimize_vars=None,
                  remove_internal=True, remove_export_type=True):
    # no_optimize_vars: 不能移除的变量名的列表
    # remove_internal: 移除执行代码本身时产生的内部代码
    # remove_export_type: 移除无用的类型导出，如str(var)
    graph = VarGraph(codes,code_vars,no_optimize_vars)
    statement_cnt = len(graph.statements)
    while True:
        graph.optimize(remove_internal,remove_export_type)
        #from pprint import pprint;pprint(graph.statements);print()
        if statement_cnt == len(graph.statements):
            break
        statement_cnt = len(graph.statements)
    return graph.get_code()

def test():
    print(optimize_code("""\
temp_var = [1,2,3]
unused_var = func(temp_var)""".splitlines(),
            [("temp_var",[]),
             ("unused_var",["temp_var"])]))

if __name__=="__main__":test()