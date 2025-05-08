import functools,itertools,types
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

TRIVIAL_TYPES = (int, float, str, bytes, bytearray, list,
                 tuple, dict, set, type(None), type(range(0)), slice)
INDENT = 4
NOCODE_EXPORT_ATTRS = ["__class__","__dict__"] # 不留下代码记录的导出属性
DEFAULT_EXPORT_FUNCS = [] # 在magic_meth_chained中自动生成

def unproxy_obj(obj):
    if _isinstance(obj, ProxiedObj):
        obj = obj._ProxiedObj__target_obj
    return obj

def unproxy_obj_recursive(obj): # 递归解除obj的代理（备用函数）
    while _isinstance(obj, ProxiedObj):
        obj = obj._ProxiedObj__target_obj
    # 递归处理容器
    if _isinstance(obj, dict):
        return {unproxy_obj_recursive(k): unproxy_obj_recursive(v)
                for k, v in obj.items()}
    elif _isinstance(obj, list):
        return [unproxy_obj_recursive(item) for item in obj]
    elif _isinstance(obj, tuple):
        return tuple(unproxy_obj_recursive(item) for item in obj)
    elif _isinstance(obj, set):
        return {unproxy_obj_recursive(item) for item in obj}
    else:
        return obj
def accept_raw_obj(func,process_arg=None,process_kw=None,process_ret=None):
    # 装饰器，用于有target_obj时只接受原始对象而不是ProxiedObj的函数（备用）
    @functools.wraps(func)
    def inner(*args,**kw):
        args = unproxy_obj_recursive(args)
        kw = unproxy_obj_recursive(kw)

        if process_arg is not None:
            args = process_arg(args)
        if process_kw is not None:
            kw = process_kw(kw)

        if kw:
            result = func(*args,**kw)
        else:
            result = func(*args)
        if process_ret is not None:
            result = process_ret(result)
        return result
    return inner

class _EmptyTarget:
    def __bool__(self):return False
EMPTY_OBJ = _EmptyTarget() # 空对象的特殊值
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

def basic_repr(obj):
    # 避免普通repr()的无限递归
    if type(obj) in TRIVIAL_TYPES:
        return repr(obj)
    return object.__repr__(obj)

def is_trivial_obj(obj): # 检查对象能否被repr()表示（即对象必须是基本类型）
    if _isinstance(obj, ProxiedObj):
        obj = obj._ProxiedObj__target_obj
        if obj is EMPTY_OBJ:return True
    if type(obj) not in TRIVIAL_TYPES: # 不使用isinstance（由于不能是基本类型子类）
        return False
    if type(obj) in (list, tuple, dict, set):
        if isinstance(obj, dict):
            obj = itertools.chain(obj.keys(), obj.values())
        return all(is_trivial_obj(sub) for sub in obj)
    return True

def is_builtin_type(cls): # 备用函数
    if get_type_flag is not None:
        flag = get_type_flag(cls)
        if not flag & Py_TPFLAGS_HEAPTYPE or flag & _Py_TPFLAGS_STATIC_BUILTIN:
            return True
        return False
    else:
        return True
        #if cls in vars(builtins).values() or cls in vars(types).values():
        #    return True
    #return False

def proxyCls(T=_EmptyTarget, chain=EMPTY_OBJ, fromvar=None):
    # 泛型，proxyCls(T)生成类型信息为T的继承自ProxiedObj的类
    if T is EMPTY_OBJ:
        return ProxiedObj

    class ProxyCls(ProxiedObj): # 创建同时从ProxiedObj与T继承的类
        # pylint: disable=unused-private-member
        __proto = T # 自身使用的原型
        def __new__(cls,*args,**kw):
            _chain = args[0] if args else kw.get("chain")
            if not _isinstance(_chain,ObjChain) and chain is not EMPTY_OBJ:
                var = chain.new_var(T.__name__)
                if fromvar is not None:
                    # pylint: disable=self-cls-assignment
                    cls = chain.add_existing_obj(T,var,f"{var} = {fromvar}.__class__",
                                                 [fromvar])
                else:
                    cls = chain.add_existing_obj(T,var, # pylint: disable=self-cls-assignment
                        f"# class {var}: {shortrepr(cls,repr_func=basic_repr)}")
                if len(args) == 3 and isinstance(T,type):
                    args=(args[0],tuple(unproxy_obj(cls) for cls in args[1]),args[2])

                if kw:return cls(*args,**kw)
                return cls(*args) # 返回ProxyCls
            else:
                return ProxiedObj.__new__(cls,*args,**kw)

    return ProxyCls

class ObjChain:
    def __init__(self, export_funcs = None, export_attrs = None,
                 export_trivial_obj = False, hook_inheritance = False,
                 hook_method_call = False):
        # ObjChain()的export_funcs和export_attrs作用于当前链的所有对象
        self.codes = []
        self.indent = 0 # 代码缩进格数（暂未使用）
        self.scope = {} # 上次执行的命名空间
        self.export_funcs = {} # 哪些函数需要导出（键为对象的变量名，值为属性名的列表，属性名可用"."分隔）
        self.export_attrs = {} # 哪些属性需要导出（键为对象的变量名）
        self.custom_export_func_check = {} # 自定义导出名称检测的回调函数
        self.custom_export_attr_check = {}
        self.exported_vars = {} # 导出的变量的字典，键为对象的id()，值为变量名（仅用于有target_obj时）
        self.proxies = {} # 键为id()，值为ProxiedObj
        # 对于所有对象，必须导出的属性
        self.export_funcs_global = export_funcs if export_funcs is not None else []
        self.export_attrs_global = export_attrs if export_attrs is not None else []
        self._var_num = 0 # 变量序号
        self.code_vars = [] # 每行代码修改和依赖于的变量，例如[("result_var",["depend_var1",...],{}),...]，{}为额外信息
        self.code_executed = [] # 代码是否已执行过（确保代码只执行一次）
        self._is_evaluating = False # 当前是否正在执行调用（用于代码的_internal信息）
        self.export_trivial_obj = export_trivial_obj # 是否不使用ProxiedObj包装基本类型（如整数、列表等）
        self.hook_inheritance = hook_inheritance # 是否继续hook从ProxiedObj包装的类继承的新类
        self.hook_method_call = hook_method_call # 是否hook实例方法的调用
    def add_code(self,code_line,result_var=None,dependency_vars=None,
                 executed=True,**extra_info):
        if dependency_vars is None:
            dependency_vars = []
        self.codes.append(" "*(self.indent*INDENT)+code_line)
        if "_internal" not in extra_info:
            extra_info["_internal"] = self._is_evaluating # _internal: 是否是执行其他生成代码时，递归生成的
        self.code_vars.append((result_var,dependency_vars,extra_info))
        self.code_executed.append(executed)
    def detect_dependency_vars(self,*iterables):
        # 自动检测依赖的变量，返回变量名的列表和未知对象的列表
        result = []; unknown = []
        for obj in itertools.chain(*iterables):
            if _isinstance(obj,ProxiedObj):
                self._assert_assoc_with(obj) # 确保关联到自身
                result.append(obj._ProxiedObj__name)
            elif id(obj) in self.exported_vars:
                result.append(self.exported_vars[id(obj)])
            else:
                unknown.append(obj)
        return result, unknown
    def _detect_var_and_add_obj(self,*iterables):
        dependency_vars, unknown = self.detect_dependency_vars(*iterables)
        for obj in unknown:
            if not is_trivial_obj(obj): # 不是repr能表示的基本类型（如整数、列表）
                new_var = self.new_var()
                self.add_imported_obj(obj,new_var) # 直接添加到自身
                dependency_vars.append(new_var)
        return dependency_vars

    # 对象处理
    def new_object(self,statement,name,dependency_vars=None,export_funcs=None,
                   export_attrs=None,use_target_obj=True,extra_info=None,
                   export_trivial_obj=None,custom_export_func=None,
                   custom_export_attr=None):
        # use_target_obj: 是否为启用target_obj的模式。为False时会暂存所有添加的代码再一并执行，
        # 为True时会在每次操作都执行一次代码，对目标对象操作一次

        # 预处理参数
        if export_trivial_obj is None:
            export_trivial_obj = self.export_trivial_obj
        if export_funcs is None:export_funcs = []
        if export_attrs is None:export_attrs = []
        self.export_funcs[name] = export_funcs # 添加对象的要导出的函数
        self.export_attrs[name] = export_attrs
        if custom_export_func is not None:
            self.custom_export_attr_check[name] = custom_export_func
        if custom_export_attr is not None:
            self.custom_export_attr_check[name] = custom_export_attr

        self.add_code(statement,name,dependency_vars,**(extra_info or {}),
                      executed = use_target_obj)
        if not use_target_obj:
            result = EMPTY_OBJ
        else:
            exec(statement,self.scope)
            result = self.scope[name]
        return proxyCls(type(result),self,name)(self,name,result,
                                                export_trivial_obj=export_trivial_obj)
    def add_existing_obj(self,obj,name,statement=None,dependency_vars=None,
                         export_funcs=None,export_attrs=None,extra_info=None,
                         export_trivial_obj=None,_export_call=False,
                         custom_export_func=None,custom_export_attr=None): # 添加现有的对象
        # 预处理参数
        if statement is None:
            statement = f"# predefined {name}: {shortrepr(obj)}"
        if export_trivial_obj is None:
            export_trivial_obj = self.export_trivial_obj
        if export_funcs is None:export_funcs = []
        if export_attrs is None:export_attrs = []
        self.export_funcs[name] = export_funcs
        self.export_attrs[name] = export_attrs
        if custom_export_func is not None:
            self.custom_export_attr_check[name] = custom_export_func
        if custom_export_attr is not None:
            self.custom_export_attr_check[name] = custom_export_attr

        self.add_code(statement,name,dependency_vars,**(extra_info or {}))
        self.scope[name] = proxyCls(type(obj),self,name)(self, name, obj, _export_call,
                                                         export_trivial_obj = export_trivial_obj)
        return self.scope[name]
    def add_exported_obj(self,obj,name): # 添加已导出的对象，仅更新exported_vars
        self.exported_vars[id(obj)] = name
    def add_imported_obj(self,obj,name,statement=None,extra_info=None): # 添加导入的外部对象，会增加一行代码
        if statement is None:
            statement = f"# external {name}: {shortrepr(obj,repr_func=basic_repr)}"
        self.add_exported_obj(obj,name)
        self.add_code(statement,name,**(extra_info or {}))
        self.scope[name] = obj
    def set_exports(self, varname, export_funcs, export_attrs):
        # 设置导出的函数和属性列表，export_funcs和export_attrs必须为列表类型
        self.export_funcs[varname] = export_funcs
        self.export_attrs[varname] = export_attrs
    def _assert_assoc_with(self,obj): # 检测其他ProxiedObj是否关联到自身
        if obj._ProxiedObj__chain is not self:
            raise ValueError("chain.get_repr(obj): obj is not associated with this chain")
    def get_target(self,obj): # 获取ProxiedObj的目标对象
        if not _isinstance(obj,ProxiedObj):
            raise TypeError("obj should be an instance of ProxiedObj")
        self._assert_assoc_with(obj)
        target = obj._ProxiedObj__target_obj
        if target is EMPTY_OBJ:return None
        return target

    # 杂项
    def new_var(self,name=None,export=False): # 申请一个新变量名
        if name is None:
            if not export:
                name=f"var{self._var_num}"
            else:
                name=f"ex_var{self._var_num}"
            self._var_num += 1
            return name
        else:
            if name not in self.scope:
                return name
            num = 0
            while True:
                varname = f"{name}{num}"
                if varname not in self.scope:
                    return varname
                num += 1
    def get_repr(self,obj): # 用于代码生成中的repr，如果对象是ProxiedObj，则直接返回对应的变量名
        if _isinstance(obj,ProxiedObj):
            self._assert_assoc_with(obj)
            return obj._ProxiedObj__name
        else:
            if id(obj) in self.exported_vars:
                return self.exported_vars[id(obj)] # 已知的导出变量
            return repr(obj)
    def is_export_func(self,func_name,var_name=None):
        # 是否为导出的函数（即下一步ProxiedObj的__export_call会设为True）
        if var_name in self.custom_export_func_check:
            return self.custom_export_func_check[var_name]() # 自定义的检测规则
        if func_name in DEFAULT_EXPORT_FUNCS: # 必须导出的函数，如__str__等
            return True
        if func_name in self.export_funcs_global:
            return True
        if var_name in self.export_funcs:
            return func_name in self.export_funcs[var_name]
        return False
    def is_export_attr(self,attr,var_name=None):
        # 是否为导出属性（即下一步getattr不返回ProxiedObj，直接返回结果）
        if var_name in self.custom_export_attr_check:
            return self.custom_export_attr_check[var_name]()
        if attr in NOCODE_EXPORT_ATTRS: # 无target_obj模式时
            return True
        if attr in self.export_attrs_global:
            return True
        if var_name in self.export_attrs:
            return attr in self.export_attrs[var_name]
        return False
    def update_exports(self,name,attr,new_var):
        # ProxiedObj的__getattr__被调用时，设置下一个对象new_var的导出
        if name in self.export_funcs:
            self.export_funcs[new_var] = []
            for exp in self.export_funcs[name]:
                attrs = exp.split(".")
                if attrs[0] == attr and len(attrs) > 1:
                    self.export_funcs[new_var].append(".".join(attrs[1:]))
        if name in self.export_attrs:
            self.export_attrs[new_var] = []
            for exp in self.export_attrs[name]:
                attrs = exp.split(".")
                if attrs[0] == attr and len(attrs) > 1:
                    self.export_attrs[new_var].append(".".join(attrs[1:]))

    # 代码执行
    def get_code(self, start_lineno=None, end_lineno=None,
                 _only_not_executed=False):
        # 获取指定行号范围的代码段
        if start_lineno is None:start_lineno = 0
        if end_lineno is None:end_lineno = len(self.codes)
        if _only_not_executed:
            codes = [self.codes[i] for i in range(start_lineno, end_lineno) \
                     if not self.code_executed[i]]
            for i in range(start_lineno, end_lineno):
                self.code_executed[i] = True
        else:
            codes = self.codes[start_lineno:end_lineno]
        return "\n".join(codes)
    def get_optimized_code(self, no_optimize_vars=None, remove_internal=True,
                           remove_export_type=True):
        return optimize_code(self.codes, self.code_vars, no_optimize_vars,
                             remove_internal, remove_export_type)
    def eval_value(self,var_name=None,end_lineno=None):
        # 一次性执行未执行过的代码（仅用于没有target_obj时）
        if end_lineno is None:end_lineno = len(self.codes)

        exec(self.get_code(end_lineno = end_lineno, _only_not_executed = True),
             self.scope)
        if var_name is not None:
            return self.scope[var_name]
        return None
    def _get_new_targetobj(self,target_obj,var_name=None,
                           result_getter_func=None,export=False,
                           use_exported_obj=False):
        # 依赖于最后一行代码，要求调用之前先调用了add_code
        # var_name为None时，返回None（此时不可使用返回值）
        if result_getter_func is not None and var_name is None:
            raise ValueError("result_getter_func requires var_name")

        pre_is_evaluating = self._is_evaluating
        self._is_evaluating = True # 记录当前正在执行其他代码

        new_code = self.codes[-1]
        cur_idx = -1
        if target_obj is not EMPTY_OBJ:
            # 一次执行完前面的全部代码
            self.eval_value(end_lineno = cur_idx) # 不包括最后一行新加入的代码
            self.code_executed[cur_idx] = True # 最后一行设为已执行过

            # 实时操作对象，并返回操作结果
            if result_getter_func is not None:
                result = result_getter_func() # 从外部函数获取返回结果（比exec更快）
                self.scope[var_name] = result # 将结果存入为scope的变量（此时var_name不为None）
            else:
                if export or use_exported_obj: # use_exported_obj: 是否在不导出时也在exec用target_obj作为变量，避免递归
                    scope = {}
                    for var in self.code_vars[cur_idx][1]: # 导出时，不使用ProxiedObj执行，避免递归
                        if _isinstance(self.scope[var],ProxiedObj):
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
        else:
            result = EMPTY_OBJ

        self._is_evaluating = pre_is_evaluating
        return result # result须不为ProxiedObj类型

def magic_meth_chained(fmt = None, use_newvar = True, indent_delta = 0,
                       export = False, use_exported_obj = True, default_fmt = False):
    # fmt: 代码的格式，{_var}表示新变量，{_self}表示自身变量
    # use_newvar: 是否会生成新的返回值变量，为False时用于+=, -=等运算符
    # indent_delta: 缩进的变化量。export: 是否返回ProxiedObj外的其他类型
    # default_fmt: 自动生成代码的格式，此时use_target_obj总是为True
    if not use_newvar and export:
        raise ValueError("can't disable use_newvar while export is set to True")
    def magic_meth_chained_inner(meth):
        if export:
            DEFAULT_EXPORT_FUNCS.append(meth.__name__) # 自动生成常量DEFAULT_EXPORT_FUNCS
        @functools.wraps(meth)
        def override(self, *args, **kw):
            nonlocal use_exported_obj
            chain = self._ProxiedObj__chain
            name = self._ProxiedObj__name
            meth_name = meth.__name__
            target_obj = self._ProxiedObj__target_obj
            no_target_obj = target_obj is EMPTY_OBJ

            # ReprFormatProxy：自定义!r格式化的行为
            fmt_kw = {key:ReprFormatProxy(val,chain.get_repr) for key,val in kw.items()}
            fmt_kw["_self"] = name
            if use_newvar:
                new_var = chain.new_var(export=export) # 申请一个新变量名
                fmt_kw["_var"] = new_var
            else:
                new_var = None

            depend_vars = chain._detect_var_and_add_obj((self,), args, kw.values())
            if fmt is not None:
                fmt_args = [ReprFormatProxy(arg,chain.get_repr) for arg in args]
                new_code = fmt.format(*fmt_args, **fmt_kw)
                chain.add_code(new_code, new_var, depend_vars, _export_type = export,
                               executed = not no_target_obj) # 加入新的一行代码
            elif default_fmt: # 自动生成格式
                use_exported_obj = True # 此时use_target_obj总是为True
                if use_newvar:
                    new_code = "{} = {}.{}({})".format(
                        new_var,name,meth_name,format_func_call(args,kw,chain.get_repr))
                else:
                    new_code = "{}.{}({})".format(
                        name,meth_name,format_func_call(args,kw,chain.get_repr))
                chain.add_code(new_code, new_var, depend_vars, _export_type = export,
                               executed = not no_target_obj)
            else:
                pass #new_code = ""

            chain.indent += indent_delta # 变化缩进


            # 不使用use_exported_obj时，result总是为None
            result = chain._get_new_targetobj(target_obj,new_var,
                                              export=export,
                                              use_exported_obj=use_exported_obj)

            if export or (self._ProxiedObj__export_trivial_obj
                          and is_trivial_obj(result)):
                if use_newvar:
                    chain.add_exported_obj(result, new_var) # 继续追踪导出的值
                if target_obj is not EMPTY_OBJ:
                    return result
                else:
                    result = chain.eval_value(new_var) # 逐行一次性执行代码，并返回结果
                    return result
            if use_newvar:
                return proxyCls(type(result),self._ProxiedObj__chain,new_var)(chain,new_var,
                            result,export_trivial_obj=self._ProxiedObj__export_trivial_obj)
            return self

        return override
    return magic_meth_chained_inner

class ProxiedObj:
    # 代理其他对象的类（建议使用ObjChain的new_object和add_existing_obj方法，而不是实例化本类）
    # 如果有target_obj，则内部应使用泛型proxyCls(T)替代ProxiedObj类，
    # 避免isinstance检测返回False
    def __init__(self,chain,name,target_obj=EMPTY_OBJ,
                 _export_call=False,export_trivial_obj=False):
        # target_obj: 要操作（代理）的目标对象，可选
        # _export_call: 当前对象的__call__是否会导出真正的结果（而不是下一个ProxiedObj）
        if "_ProxiedObj__chain" in object.__getattribute__(self,"__dict__"):
            return # 已经初始化过
        self.__chain=chain
        self.__name=name
        self.__export_call=_export_call
        if not _export_call and self.__chain.hook_method_call \
                and isinstance(target_obj,types.MethodType):
            obj = target_obj.__self__
            if id(obj) in self.__chain.proxies:
                target_obj = types.MethodType(target_obj.__func__,
                                              self.__chain.proxies[id(obj)]) # 修改方法的对象为代理对象
        self.__target_obj=target_obj
        if target_obj is not EMPTY_OBJ:
            self.__chain.proxies[id(target_obj)] = self

        self.__export_trivial_obj=export_trivial_obj
        # pylint: disable=unused-private-member
        self.__no_self_attr = True # 不再使用自身的属性
    def __call__(self,*args,**kw):
        depend_vars = self.__chain._detect_var_and_add_obj((self,), args, kw.values())
        new_var = self.__chain.new_var()
        new_code = "{} = {}({})".format(
            new_var, self.__name, format_func_call(args,kw,self.__chain.get_repr))
        self.__chain.add_code(new_code, new_var, depend_vars, # 添加代码
                              executed = self.__target_obj is not EMPTY_OBJ\
                                         and not self.__export_call)

        if self.__export_call:
            result = self.__chain.eval_value(new_var)
        else:
            def _getter():
                if kw:
                    return self.__target_obj(*args,**kw)
                else:
                    return self.__target_obj(*args) # 避免对不接收关键字参数的函数传递关键字
            result = self.__chain._get_new_targetobj(self.__target_obj,new_var,_getter)

        if self.__export_call or (self.__export_trivial_obj
                                  and is_trivial_obj(result)):
            self.__chain.add_exported_obj(result, new_var)
            return result # 直接返回结果，不继续返回ProxiedObj

        if isinstance(self.__target_obj,type) and isinstance(result,self.__target_obj):
            # 自身是类且result为自身的实例化对象，则实例使用类的导出函数、属性
            if self.__name in self.__chain.export_attrs:
                self.__chain.export_attrs[new_var] = self.__chain.\
                                                     export_attrs[self.__name].copy()
            if self.__name in self.__chain.export_funcs:
                self.__chain.export_funcs[new_var] = self.__chain.\
                                                     export_funcs[self.__name].copy()
        return proxyCls(type(result),self.__chain,self.__name)(self.__chain,new_var,
                                    result,export_trivial_obj=self.__export_trivial_obj)

    #@magic_meth_chained("{_var} = {_self}.{}")
    def __getattr__(self,attr):
        if "_ProxiedObj__chain" not in object.\
                __getattribute__(self,"__dict__"): # self尚未初始化
            return object.__getattribute__(self,attr)
        if attr in NOCODE_EXPORT_ATTRS and self.__target_obj is not EMPTY_OBJ:
            return getattr(self.__target_obj, attr) # 不留下代码的直接导出属性

        new_var=self.__chain.new_var()
        new_code = f"{new_var} = {self.__name}.{attr}"
        self.__chain.add_code(new_code, new_var, [self.__name],
                              executed = self.__target_obj is not EMPTY_OBJ)

        export = self.__chain.is_export_attr(attr, self.__name)
        result = self.__chain._get_new_targetobj(
                self.__target_obj,new_var,lambda:getattr(self.__target_obj,attr),
                export = export) # 获取结果对象
        if export:
            return result

        if self.__export_trivial_obj and is_trivial_obj(result)\
                or self.__chain.is_export_attr(attr,self.__name):
            self.__chain.add_exported_obj(result, new_var)
            return result # 直接返回结果，不继续返回ProxiedObj
        else:
            self.__chain.update_exports(self.__name, attr, new_var)

        return proxyCls(type(result),self.__chain,self.__name)(
                            self.__chain,new_var,result,
                            self.__chain.is_export_func(attr,self.__name),
                            self.__export_trivial_obj)
    @magic_meth_chained("{_var} = str({_self})",export=True)
    def __str__(self): pass
    @magic_meth_chained("{_var} = repr({_self})",export=True)
    def __repr__(self): pass
    @magic_meth_chained("{_var} = dir({_self})",export=True)
    def __dir__(self): pass
    @magic_meth_chained("{_self}.{} = {!r}", False)
    def __setattr_override(self,attr,value):pass
    def __setattr__(self,attr,value):
        dct = object.__getattribute__(self,"__dict__")
        if not dct.get("_ProxiedObj__no_self_attr",False):
            object.__setattr__(self,attr,value)
        else:
            self.__setattr_override(attr,value)
    def __getattribute__(self,attr):
        result = object.__getattribute__(self,attr)
        if object.__getattribute__(self,"__dict__").get(
                "_ProxiedObj__no_self_attr",False) \
                and not attr.startswith("_ProxiedObj"):
            raise AttributeError # 改用__getattr__
        return result
    def __new__(cls,*args,**kw):
        if len(args) >= 3:
            target_obj = args[2]
        elif "target_obj" in kw:
            target_obj = kw["target_obj"]
        else:
            target_obj = EMPTY_OBJ
        if _isinstance(target_obj, ProxiedObj):
            return target_obj # 避免重复包装对象，提高性能
        return object.__new__(cls)

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
    @magic_meth_chained("{_var} = {_self} < {!r}",export=True)
    def __lt__(self, other): pass
    @magic_meth_chained("{_var} = {_self} <= {!r}",export=True)
    def __le__(self, other): pass
    @magic_meth_chained("{_var} = {_self} == {!r}",export=True)
    def __eq__(self, other): pass
    @magic_meth_chained("{_var} = {_self} != {!r}",export=True)
    def __ne__(self, other): pass
    @magic_meth_chained("{_var} = {_self} > {!r}",export=True)
    def __gt__(self, other): pass
    @magic_meth_chained("{_var} = {_self} >= {!r}",export=True)
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
    @magic_meth_chained(default_fmt=True,export=True)
    def __fspath__(self):pass

_isinstance = isinstance
from pyobject.objproxy.builtin_hook import hook_builtins # pylint: disable=ungrouped-imports
hook_builtins() # hook内置函数

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
