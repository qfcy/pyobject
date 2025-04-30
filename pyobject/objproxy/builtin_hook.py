# 内置函数和少数标准库函数的hook
import builtins,_collections_abc
import collections.abc as collections_abc
from pyobject.objproxy import ProxiedObj,accept_raw_obj

_range = type(range(0)) #range
def range(*args):
    return _range(*(int(arg) for arg in args)) # 修复默认range的cannot be interpreted as integer

_pre_build_class = __build_class__
def __build_class__(func, cls_name, *bases, metaclass=None, **kwds):
    bases = list(bases)
    hook_inheritance = False
    chain = None
    dependency = []
    for i, cls in enumerate(bases):
        if isinstance(cls, ProxiedObj):
            bases[i] = cls._ProxiedObj__target_obj
            if chain is not None and cls._ProxiedObj__chain is not chain:
                raise ValueError("base classes should be associated with the same chain")
            chain = cls._ProxiedObj__chain
            hook_inheritance |= chain.hook_inheritance
            dependency.append(cls._ProxiedObj__name)
    if metaclass is None:
        result = _pre_build_class(func, cls_name, *bases, **kwds)
    else:
        result = _pre_build_class(func, cls_name, *bases, metaclass=metaclass,**kwds)
    if hook_inheritance:
        var_name = chain.new_var(cls_name)
        hooked_result = chain.add_existing_obj(result, var_name,
            f"# Created inherited class {cls_name!r} from {', '.join(map(repr,dependency))}",
            dependency)
        return hooked_result
    return result

_isinstance = isinstance
_issubclass = issubclass
_callable = callable
_getattr = getattr
def isinstance(obj, class_or_tuple):
    if _isinstance(class_or_tuple, ProxiedObj):
        class_or_tuple = class_or_tuple._ProxiedObj__target_obj
    if _isinstance(class_or_tuple, tuple):
        class_or_tuple = tuple(cls._ProxiedObj__target_obj \
            if _isinstance(cls, ProxiedObj) else cls \
            for cls in class_or_tuple)
    result = _isinstance(obj, class_or_tuple)
    if not result:
        # 将obj和class_or_tuple从ProxiedObj转换为普通对象，再调用_isinstance
        if _isinstance(obj, ProxiedObj):
            obj = obj._ProxiedObj__target_obj
        return _isinstance(obj, class_or_tuple) # 重新调用_isinstance
    return result
def issubclass(cls, class_or_tuple):
    if _isinstance(class_or_tuple, ProxiedObj):
        class_or_tuple = class_or_tuple._ProxiedObj__target_obj
    if _issubclass(cls, ProxiedObj):
        proto = getattr(cls, "_ProxyCls__proto", None)
        if proto is not None:
            return _issubclass(proto, class_or_tuple)
    return _issubclass(cls, class_or_tuple)
def callable(obj):
    if _isinstance(obj, ProxiedObj):
        obj = obj._ProxiedObj__target_obj
    return _callable(obj)
def getattr(*args,**kw):
    if isinstance(args[1],ProxiedObj):
        args = (args[0], args[1]._ProxiedObj__target_obj, *args[2:])
    if "name" in kw and isinstance(kw["name"],ProxiedObj):
        kw["name"] = kw["name"]._ProxiedObj__target_obj
    return _getattr(*args)

_pre_check_methods = _collections_abc._check_methods
def _check_methods(Cls, *methods):
    if issubclass(Cls, ProxiedObj):
        if hasattr(Cls, "_ProxyCls__proto"):
            return _pre_check_methods(Cls._ProxyCls__proto,*methods)
        else:
            return _pre_check_methods(object,*methods) # ProxiedObj继承自object
    return _pre_check_methods(Cls,*methods)

def hook_builtins():
    builtins.range=range
    builtins.__build_class__ = __build_class__
    builtins.isinstance = isinstance
    builtins.issubclass = issubclass
    builtins.callable = callable
    builtins.getattr = getattr
    _collections_abc._check_methods = _check_methods # 修改collections.abc库
    collections_abc._check_methods = _check_methods

# 内置类型的修改（备用）
class CustomStr(builtins.str):
    __init__ = accept_raw_obj(builtins.str,lambda args:args[1:],
                              process_ret=lambda ret:None)
    __new__ = accept_raw_obj(builtins.str,lambda args:args[1:])

class CustomInt(builtins.int):
    __init__ = accept_raw_obj(builtins.int,lambda args:args[1:],
                              process_ret=lambda ret:None)
    __new__ = accept_raw_obj(builtins.int,lambda args:args[1:])

class CustomBytes(builtins.bytes):
    __init__ = accept_raw_obj(builtins.bytes,lambda args:args[1:],
                              process_ret=lambda ret:None)
    __new__ = accept_raw_obj(builtins.bytes,lambda args:args[1:])
