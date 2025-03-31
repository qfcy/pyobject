import functools,itertools
import builtins,_collections_abc,types
import collections.abc as collections_abc
from pyobject import shortrepr
from pyobject.objproxy.dynobj import DynObj
from pyobject.objproxy.optimize import optimize_code
from pyobject.objproxy.utils import *

try:from pyobject import get_type_flag
except ImportError:get_type_flag=None
try:from timer_tool import timer # pip install timer-tool
except ImportError:timer=lambda func:func

# 来自CPython的object.h
_Py_TPFLAGS_STATIC_BUILTIN = 1 << 1 # 3.12+
Py_TPFLAGS_HEAPTYPE = 1 << 9
INDENT = 4

# -- 替换内置方法 --
_range = range
def range(*args):
    return _range(*(int(arg) for arg in args)) # 修复默认range的cannot be interpreted as integer
builtins.range=range

_pre_check_methods = _collections_abc._check_methods
def _check_methods(Cls, *methods):
    if issubclass(Cls, ProxiedObj):
        if hasattr(Cls, "_ProxyCls__base"):
            return _pre_check_methods(Cls._ProxyCls__base,*methods)
        else:
            return _pre_check_methods(object,*methods) # ProxiedObj继承自object
    return _pre_check_methods(Cls,*methods)
_collections_abc._check_methods = _check_methods # 修改collections.abc库
collections_abc._check_methods = _check_methods


class EmptyTarget:pass
EMPTY_OBJ = EmptyTarget() # 空对象的特殊值
class ReprFormatProxy:
    def __init__(self,target_obj,repr_func):
        self.target_obj = target_obj
        self.repr_func = repr_func
    def __format__(self, spec):
        if spec == "r": # 自定义!r的格式化
            return self.repr_func(self.target_obj)
        return self.target_obj.__format__(spec)
    def __repr__(self):
        return self.repr_func(self.target_obj)

def proxyCls(obj=None):
    if obj is None or get_type_flag is None:
        return ProxiedObj
    if not isinstance(obj,type): # obj不是类
        obj = type(obj)
    try:
        flag = get_type_flag(obj)
        #if obj in vars(builtins).values() or obj in vars(types).values():
        if not flag & Py_TPFLAGS_HEAPTYPE or flag & _Py_TPFLAGS_STATIC_BUILTIN: # 内置类
            return ProxiedObj

        class ProxyCls(ProxiedObj,obj): # 创建同时从ProxiedObj与target_obj继承的类
            __base = obj

        #mro = ProxyCls.__mro__
        #set_type_mro(ProxyCls, (ProxyCls,) + ProxiedObj.__mro__) # 实际上isinstance会检测__mro__
    except TypeError: # 无法继承
        ProxyCls = ProxiedObj

    return ProxyCls

class ObjChain:
    def __init__(self, export_funcs = None, export_attrs = None):
        # ObjChain()的export_funcs和export_attrs作用于当前链的所有对象
        self.codes = []
        self.indent = 0 # 暂未使用
        self.exec_lineno = 0 # 导出中上次执行到的行号（确保代码只执行一次）
        self.scope = {} # 上次执行的命名空间
        self.export_funcs = {} # 哪些函数需要导出（键为对象的变量名，由于变量名是唯一的）
        self.export_attrs = {} # 哪些属性需要导出（键为对象的变量名）
        self.exported_vars = {} # 导出的变量的字典，键为对象的id()，值为变量名（仅用于有target_obj时）
        # 对于所有对象，必须导出的属性
        self.export_funcs_global = export_funcs if export_funcs is not None else []
        self.export_attrs_global = export_attrs if export_attrs is not None else []
        self._pre_without_target = True # 之前的对象是没有目标对象的
        self._var_num = 0 # 变量序号
        self.code_vars = [] # 每行代码修改和依赖于的变量，例如[("result_var",["depend_var1",...],{}),...]，{}为额外信息
        self._is_evaluating = False # 当前是否正在执行调用
    def add_code(self,code_line,result_var=None,dependency_vars=None,
                 **extra_info):
        if dependency_vars is None:
            dependency_vars = []
        self.codes.append(" "*(self.indent*INDENT)+code_line)
        extra_info["_internal"] = self._is_evaluating # _internal: 是否是执行其他生成代码时，递归生成的
        self.code_vars.append((result_var,dependency_vars,extra_info))
    def _detect_dependency_vars(self,*iterables):
        result = []
        for obj in itertools.chain(*iterables):
            if isinstance(obj,ProxiedObj):
                self._assert_assoc_with(obj) # 确保关联到自身
                result.append(obj._ProxiedObj__name)
            elif id(obj) in self.exported_vars:
                result.append(self.exported_vars[id(obj)])
        return result

    # 对象处理
    def new_object(self,code_line,name,export_funcs=None,
                   export_attrs=None,use_target_obj=True):
        self.add_code(code_line,name)
        if export_funcs is None:export_funcs = []
        if export_attrs is None:export_attrs = []
        self.export_funcs[name] = export_funcs # 添加到对象的要导出的函数
        self.export_attrs[name] = export_attrs
        if not use_target_obj:
            result = EMPTY_OBJ
        else:
            exec(code_line,self.scope)
            result = self.scope[name]
            self.exec_lineno = len(self.codes)
        return proxyCls(result)(self,name,target_obj=result)
    def add_existing_obj(self,obj,name): # 添加已有的对象
        self.add_code(f"# predefined {name}: {shortrepr(obj)}",name)
        self.scope[name] = proxyCls(obj)(self, name, target_obj=obj)
        return self.scope[name]
    def _assert_assoc_with(self,obj): # 检测其他ProxiedObj是否关联到自身
        if obj._ProxiedObj__chain is not self:
            raise ValueError("chain.get_repr(obj): obj is not associated with this chain")
    def get_target(self,obj): # 获取ProxiedObj的目标对象
        if not isinstance(obj,ProxiedObj):
            raise TypeError("obj should be an instance of ProxiedObj")
        self._assert_assoc_with(obj)
        target = obj._ProxiedObj__target_obj
        if target is EMPTY_OBJ:return None
        return target

    # 杂项
    def new_var(self,export=False): # 申请一个新变量名
        if not export:
            name=f"var{self._var_num}"
        else:
            name=f"ex_var{self._var_num}"
        self._var_num += 1
        return name
    def get_repr(self,obj): # 用于代码生成中的repr，如果对象是ProxiedObj，则直接返回对应的变量名
        if isinstance(obj,ProxiedObj):
            self._assert_assoc_with(obj)
            return obj._ProxiedObj__name
        else:
            if id(obj) in self.exported_vars:
                return self.exported_vars[id(obj)] # 已知的导出变量
            return repr(obj)
    def is_export_func(self,func_name,var_name=None):
        # 是否为导出的函数（即下一步ProxiedObj的__export_call会设为True）
        if func_name in self.export_funcs_global:
            return True
        if var_name in self.export_funcs:
            return func_name in self.export_funcs[var_name]
        return False
    def is_export_attr(self,attr,var_name=None):
        # 是否为导出属性（即下一步getattr不返回ProxiedObj，直接返回结果）
        if attr in self.export_attrs_global:
            return True
        if var_name in self.export_attrs:
            return attr in self.export_attrs[var_name]
        return False

    # 代码执行
    def get_code(self, start_lineno=None, end_lineno=None):
        # 获取指定行号范围的代码段
        if start_lineno is None:start_lineno = 0
        if end_lineno is None:end_lineno = len(self.codes)
        return "\n".join(self.codes[start_lineno:end_lineno])
    def get_optimized_code(self, no_optimize_vars=None, remove_internal=True,
                           remove_export_type=True):
        return optimize_code(self.codes, self.code_vars, no_optimize_vars,
                             remove_internal, remove_export_type)
    def eval_value(self,var_name=None,end_lineno=None):
        # 一次性执行未执行过的代码（仅用于没有target_obj时）
        if end_lineno is None:end_lineno = len(self.codes)

        exec(self.get_code(self.exec_lineno,end_lineno),self.scope) # 从exec_lineno继续执行后面的代码
        self.exec_lineno = end_lineno
        if var_name is not None:
            return self.scope[var_name]
        return None
    def _get_new_targetobj(self,target_obj,var_name=None,
                           result_getter_func=None,export=False,use_target_obj=False):
        # 依赖于最后一行代码，要求调用之前先调用了add_code
        # var_name为None时，返回None（此时不可使用返回值）
        if result_getter_func is not None and var_name is None:
            raise ValueError("result_getter_func requires var_name")

        pre_is_evaluating = self._is_evaluating
        self._is_evaluating = True # 记录当前正在执行其他代码

        new_code = self.codes[-1]
        if target_obj is not EMPTY_OBJ:
            # 一次执行完前面的全部代码
            if self._pre_without_target:
                self.eval_value(end_lineno = len(self.codes) - 1) # 不包括最后一行新加入的代码
            self._pre_without_target = False

            # 实时操作对象，并返回操作结果
            if result_getter_func is not None:
                result = result_getter_func() # 从外部函数获取返回结果（比exec更快）
                self.scope[var_name] = result # 将结果存入为scope的变量（此时var_name不为None）
            else:
                if export or use_target_obj: # use_target_obj: 是否在不导出时也在exec用target_obj作为变量，避免递归
                    scope = {}
                    for var in self.code_vars[-1][1]: # 导出时，不使用ProxiedObj执行，避免递归
                        if isinstance(self.scope[var],ProxiedObj):
                            self._assert_assoc_with(self.scope[var])
                            scope[var] = self.scope[var]._ProxiedObj__target_obj
                        else:
                            scope[var] = self.scope[var]
                else:
                    scope = self.scope

                exec(new_code, scope) # 执行最后一行
                if scope is not self.scope:
                    self.scope.update(scope) # 合并执行结果

                if var_name is not None:
                    result = scope[var_name] # 从scope取结果
                else:
                    result = None
            self.exec_lineno = len(self.codes) # 移到最后
        else:
            result = EMPTY_OBJ
            self._pre_without_target = True

        self._is_evaluating = pre_is_evaluating
        return result # result须不为ProxiedObj类型

def magic_meth_chained(fmt = None, use_newvar = True, indent_delta = 0,
                       export = False, use_target_obj = False, default_fmt = False):
    # use_newvar: 是否会生成新的返回值变量，为False时用于+=, -=等运算符
    # indent_delta: 缩进的变化量。export: 是否返回ProxiedObj外的其他类型
    # default_fmt: 自动生成代码的格式，此时use_target_obj总是为True
    if not use_newvar and export:
        raise ValueError("can't disable use_newvar while export is set to True")

    def magic_meth_chained_inner(meth):
        @functools.wraps(meth)
        def override(self,*args,**kw):
            nonlocal use_target_obj
            chain = self._ProxiedObj__chain
            name = self._ProxiedObj__name
            meth_name = meth.__name__

            fmt_kw = {key:ReprFormatProxy(val,chain.get_repr) for key,val in kw.items()} # 自定义!r格式化的行为
            fmt_kw["_self"] = name
            if use_newvar:
                new_var = chain.new_var(export=export) # 申请一个新变量名
                fmt_kw["_var"] = new_var
            else:
                new_var = None

            if fmt is not None:
                fmt_args = [ReprFormatProxy(arg,chain.get_repr) for arg in args]
                new_code = fmt.format(*fmt_args, **fmt_kw)
                chain.add_code(new_code,new_var,chain._detect_dependency_vars(
                                (self,), args, kw.values()), _export_type = export) # 加入新的一行代码
            elif default_fmt: # 自动生成格式
                use_target_obj = True # 此时use_target_obj总是为True
                if use_newvar:
                    new_code = "{} = {}.{}({})".format(
                        new_var,name,meth_name,format_func_call(args,kw,chain.get_repr))
                else:
                    new_code = "{}.{}({})".format(
                        name,meth_name,format_func_call(args,kw,chain.get_repr))
                chain.add_code(new_code,new_var,chain._detect_dependency_vars(
                                (self,), args, kw.values()), _export_type = export)
            else:
                pass #new_code = ""

            chain.indent += indent_delta # 变化缩进

            target_obj = self._ProxiedObj__target_obj
            # 不使用use_newvar时，result总是为None
            result = chain._get_new_targetobj(target_obj,new_var,
                                              export=export,use_target_obj=use_target_obj)

            if export:
                if target_obj is not EMPTY_OBJ:
                    chain.exported_vars[id(result)] = new_var # 继续追踪导出的值
                    return result
                else:
                    result = chain.eval_value(new_var) # 逐行一次性执行代码，并返回结果
                    chain.exported_vars[id(result)] = new_var # 继续追踪
                    return result
            if use_newvar:
                return proxyCls(result)(chain,new_var,target_obj=result)
            return self

        return override
    return magic_meth_chained_inner

class ProxiedObj:
    # 代理其他对象的类
    # 如果有target_obj，则不应直接实例化ProxiedObj，
    # 需要实例化同时从ProxiedObj与target_obj继承的类（proxyCls函数），避免isinstance检测返回False
    def __init__(self,chain,name,export_call=False,target_obj=EMPTY_OBJ):
        # target_obj: 要操作（代理）的目标对象，可选
        # export_call: 当前对象的__call__是否会导出真实结果（而不是下一个ProxiedObj）
        self.__chain=chain
        self.__name=name
        self.__export_call=export_call
        self.__target_obj=target_obj
    def __call__(self,*args,**kw):
        new_var=self.__chain.new_var()
        new_code="{} = {}({})".format(
            new_var, self.__name, format_func_call(args,kw,self.__chain.get_repr))
        self.__chain.add_code(new_code,new_var,self.__chain._detect_dependency_vars(
                                    (self,), args, kw.values())) # 添加代码

        if self.__export_call:
            return self.__chain.eval_value(new_var)

        def _getter():
            if kw:
                return self.__target_obj.__call__(*args,**kw)
            else:
                return self.__target_obj.__call__(*args) # 避免对不接收关键字参数的函数传递关键字
        result = self.__chain._get_new_targetobj(self.__target_obj,new_var,_getter)

        return proxyCls(result)(self.__chain,new_var,target_obj=result)

    #@magic_meth_chained("{_var} = {_self}.{}")
    def __getattr__(self,attr):
        if "_ProxiedObj__chain" not in self.__dict__: # self尚未初始化
            return object.__getattribute__(self,attr)
        new_var=self.__chain.new_var()
        new_code = f"{new_var} = {self.__name}.{attr}"
        self.__chain.add_code(new_code,new_var,[self.__name])

        if attr in self.__chain.export_attrs.get(self.__name,[]):
            return self.__chain.eval_value(new_var)

        result = self.__chain._get_new_targetobj(
                self.__target_obj,new_var,lambda:getattr(self.__target_obj,attr))

        if self.__chain.is_export_attr(attr,self.__name):
            return result # 直接返回结果，不继续返回ProxiedObj
        return proxyCls(result)(self.__chain,new_var,
                                self.__chain.is_export_func(attr,self.__name),
                                result)
    @magic_meth_chained("{_var} = str({_self})",export=True)
    def __str__(self): pass
    @magic_meth_chained("{_var} = repr({_self})",export=True)
    def __repr__(self): pass

    # 算术运算符
    @magic_meth_chained("{_var} = {_self} + {!r}")
    def __add__(self, other): pass
    @magic_meth_chained("{_var} = {_self} - {!r}")
    def __sub__(self, other): pass
    @magic_meth_chained("{_var} = {_self} * {!r}")
    def __mul__(self, other): pass
    @magic_meth_chained("{_var} = {_self} / {!r}")
    def __truediv__(self, other): pass
    @magic_meth_chained("{_var} = {_self} // {!r}")
    def __floordiv__(self, other): pass
    @magic_meth_chained("{_var} = {_self} % {!r}")
    def __mod__(self, other): pass
    @magic_meth_chained("{_var} = {_self} ** {!r}")
    def __pow__(self, other): pass
    @magic_meth_chained("{_var} = {_self} << {!r}")
    def __lshift__(self, other): pass
    @magic_meth_chained("{_var} = {_self} >> {!r}")
    def __rshift__(self, other): pass
    @magic_meth_chained("{_var} = {_self} & {!r}")
    def __and__(self, other): pass
    @magic_meth_chained("{_var} = {_self} ^ {!r}")
    def __xor__(self, other): pass
    @magic_meth_chained("{_var} = {_self} | {!r}")
    def __or__(self, other): pass

    # 反向算术运算符
    @magic_meth_chained("{_var} = {!r} - {_self}")
    def __radd__(self, other): pass
    @magic_meth_chained("{_var} = {!r} - {_self}")
    def __rsub__(self, other): pass
    @magic_meth_chained("{_var} = {!r} * {_self}")
    def __rmul__(self, other): pass
    @magic_meth_chained("{_var} = {!r} / {_self}")
    def __rtruediv__(self, other): pass
    @magic_meth_chained("{_var} = {!r} // {_self}")
    def __rfloordiv__(self, other): pass
    @magic_meth_chained("{_var} = {!r} % {_self}")
    def __rmod__(self, other): pass
    @magic_meth_chained("{_var} = {!r} ** {_self}")
    def __rpow__(self, other): pass
    @magic_meth_chained("{_var} = {!r} << {_self}")
    def __rlshift__(self, other): pass
    @magic_meth_chained("{_var} = {!r} >> {_self}")
    def __rrshift__(self, other): pass
    @magic_meth_chained("{_var} = {!r} & {_self}")
    def __rand__(self, other): pass
    @magic_meth_chained("{_var} = {!r} ^ {_self}")
    def __rxor__(self, other): pass
    @magic_meth_chained("{_var} = {!r} | {_self}")
    def __ror__(self, other): pass

    # 增量赋值
    @magic_meth_chained("{_self} += {!r}", False)
    def __iadd__(self, other): pass
    @magic_meth_chained("{_self} -= {!r}", False)
    def __isub__(self, other): pass
    @magic_meth_chained("{_self} *= {!r}", False)
    def __imul__(self, other): pass
    @magic_meth_chained("{_self} /= {!r}", False)
    def __itruediv__(self, other): pass
    @magic_meth_chained("{_self} //= {!r}", False)
    def __ifloordiv__(self, other): pass
    @magic_meth_chained("{_self} %= {!r}", False)
    def __imod__(self, other): pass
    @magic_meth_chained("{_self} **= {!r}", False)
    def __ipow__(self, other): pass
    @magic_meth_chained("{_self} <<= {!r}", False)
    def __ilshift__(self, other): pass
    @magic_meth_chained("{_self} >>= {!r}", False)
    def __irshift__(self, other): pass
    @magic_meth_chained("{_self} &= {!r}", False)
    def __iand__(self, other): pass
    @magic_meth_chained("{_self} |= {!r}", False)
    def __ior__(self, other): pass
    @magic_meth_chained("{_self} ^= {!r}", False)
    def __ixor__(self, other): pass

    # 比较运算符
    @magic_meth_chained("{_var} = {_self} < {!r}")
    def __lt__(self, other): pass
    @magic_meth_chained("{_var} = {_self} <= {!r}")
    def __le__(self, other): pass
    @magic_meth_chained("{_var} = {_self} == {!r}")
    def __eq__(self, other): pass
    @magic_meth_chained("{_var} = {_self} != {!r}")
    def __ne__(self, other): pass
    @magic_meth_chained("{_var} = {_self} > {!r}")
    def __gt__(self, other): pass
    @magic_meth_chained("{_var} = {_self} >= {!r}")
    def __ge__(self, other): pass

    # 一元运算符
    @magic_meth_chained("{_var} = -{_self}")
    def __neg__(self): pass
    @magic_meth_chained("{_var} = +{_self}")
    def __pos__(self): pass
    @magic_meth_chained("{_var} = abs({_self})")
    def __abs__(self): pass
    @magic_meth_chained("{_var} = ~{_self}")
    def __invert__(self): pass

    # 容器/迭代器
    @magic_meth_chained("{_var} = len({_self})",export=True)
    def __len__(self): pass
    @magic_meth_chained("{_var} = {_self}[{!r}]")
    def __getitem__(self, key): pass
    @magic_meth_chained("{_self}[{!r}] = {!r}", False)
    def __setitem__(self, key, value): pass
    @magic_meth_chained("del {_self}[{!r}]", False)
    def __delitem__(self, key): pass
    @magic_meth_chained("{_var} = reversed({_self})",export=True)
    def __reversed__(self):pass
    @magic_meth_chained("{_var} = {!r} in {_self}",export=True)
    def __contains__(self, item):pass
    @magic_meth_chained("{_var} = iter({_self})",export=True)
    def __iter__(self):pass
    @magic_meth_chained("{_var} = next({_self})",export=True)
    def __next__(self):pass

    # 类型转换
    @magic_meth_chained("{_var} = int({_self})",export=True)
    def __int__(self):pass
    @magic_meth_chained("{_var} = float({_self})",export=True)
    def __float__(self):pass
    @magic_meth_chained("{_var} = complex({_self})",export=True)
    def __complex__(self):pass
    @magic_meth_chained("{_var} = round({_self}, {!r})",export=True)
    def __round__(self, ndigits=None):pass
    @magic_meth_chained("{_var} = bool({_self})",export=True)
    def __bool__(self): pass
    @magic_meth_chained("{_var} = hash({_self})",export=True)
    def __hash__(self): pass

    # 上下文管理
    #@magic_meth_chained("with {_self}:",False,1)
    @magic_meth_chained(default_fmt=True)
    def __enter__(self): pass
    #@magic_meth_chained("",False,-1)
    @magic_meth_chained(default_fmt=True,export=True)
    def __exit__(self, exc_type, exc_value, traceback): pass

    # 其他
    @magic_meth_chained(default_fmt=True,export=True)
    def __await__(self):pass
    @magic_meth_chained(default_fmt=True,export=True)
    def __aiter__(self):pass

def proxy_demo():
    chain = ObjChain(export_attrs=["__array_struct__"])
    try:
        np = chain.new_object("import numpy as np","np")
        plt = chain.new_object("import matplotlib.pyplot as plt","plt",
                               export_funcs = ["show"])

        # 测试调用伪numpy, matplotlib模块
        arr = np.array(range(1,11))
        arr_squared = arr ** 2
        mean = np.mean(arr)
        std_dev = np.std(arr)
        print(mean, std_dev)
        #arr2 = np.copy(arr)
        #arr2[0] = float(mean) # 测试复用已导出的值

        plt.plot(arr, arr_squared)
        plt.show()
    finally:
        print(f"Code:\n{chain.get_code()}\n")
        print(f"Optimized:\n{chain.get_optimized_code()}")

if __name__=="__main__":proxy_demo()