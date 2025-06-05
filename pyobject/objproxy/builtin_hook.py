# 内置函数和部分标准库函数的hook
import sys,builtins,_collections_abc,inspect
import collections.abc as collections_abc
from pyobject.objproxy import ProxiedObj

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
        if _isinstance(cls, ProxiedObj):
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
    elif _isinstance(class_or_tuple, tuple):
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
    if _isinstance(cls, ProxiedObj):
        cls = cls._ProxiedObj__target_obj
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
def getattr(*args):
    if _isinstance(args[1],ProxiedObj):
        args = (args[0], args[1]._ProxiedObj__target_obj, *args[2:])
    return _getattr(*args)

_pre_check_methods = _collections_abc._check_methods
def _check_methods(Cls, *methods):
    if issubclass(Cls, ProxiedObj):
        if hasattr(Cls, "_ProxyCls__proto"):
            return _pre_check_methods(Cls._ProxyCls__proto,*methods)
        else:
            return _pre_check_methods(object,*methods) # ProxiedObj继承自object
    return _pre_check_methods(Cls,*methods)

_super=builtins.super
class super(_super):
    def __init__(self,*args):
        # 模拟CPython typeobject.c中super()的行为
        if not args:
            frame = getattr(sys._getframe(),"f_back",None)
            if frame is None:
                raise RuntimeError("super(): no current frame")
            code = frame.f_code
            if code is None:
                raise RuntimeError("super(): no code object")
            if code.co_argcount == 0:
                raise RuntimeError("super(): no arguments")
            try:
                self_ = frame.f_locals[code.co_varnames[0]]
            except (IndexError, KeyError):
                raise RuntimeError("super(): arg[0] deleted") from None
            if "__class__" not in frame.f_locals:
                raise RuntimeError("super(): bad __class__ cell")
            cls = frame.f_locals["__class__"]
            if not isinstance(cls, type):
                raise RuntimeError("super(): __class__ is not a type (%s)" \
                                   % type(cls).__name__)
            args = (cls, self_)
        args = tuple(item._ProxiedObj__target_obj if _issubclass(
                     object.__getattribute__(item,"__class__"),
                     ProxiedObj) else item for item in args) # 确保不为ProxiedObj
        _super.__init__(self,*args)

_signature = inspect.signature
_getattr_static = inspect.getattr_static
def signature(obj, **kw):
    if _isinstance(obj, ProxiedObj):
        obj = obj._ProxiedObj__target_obj
    return _signature(obj, **kw)
def getattr_static(obj, attr, *args, **kw):
    if _isinstance(obj, ProxiedObj):
        obj = obj._ProxiedObj__target_obj
    if _isinstance(attr, ProxiedObj):
        attr = attr._ProxiedObj__target_obj
    if kw:
        return _getattr_static(obj, attr, *args, **kw)
    else:
        return _getattr_static(obj, attr, *args)

def hook_builtins():
    builtins.range=range
    builtins.__build_class__ = __build_class__
    builtins.isinstance = isinstance
    builtins.issubclass = issubclass
    builtins.callable = callable
    builtins.getattr = getattr
    builtins.super = super
    _collections_abc._check_methods = _check_methods # 修改collections.abc库
    collections_abc._check_methods = _check_methods
    inspect.signature = signature
    inspect.getattr_static = getattr_static
