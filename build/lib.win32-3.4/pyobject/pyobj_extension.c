#include <Python.h>
#include <stdint.h>

PyDoc_STRVAR(convptr_doc, u8"convptr(pointer)"
    u8"\n"
    u8"Convert a integer pointer to a Python object, as a reverse of id()."
    u8"将整数指针转换为Python对象，与id()相反。\n"
    u8"Warning:Converting an invalid pointer may lead to crashes.");
PyDoc_STRVAR(py_inc_doc, u8"py_incref(obj)"
    u8"\n"
    u8"Increase the reference count of an object."
    u8"将对象的引用计数增加1。\n"
    u8"Warning:Improper use of this function may lead to crashes.");
PyDoc_STRVAR(py_dec_doc, u8"py_decref(obj)"
    u8"\n"
    u8"Decrease the reference count of an object."
    u8"将对象的引用计数减小1。\n"
    u8"Warning:Improper use of this function may lead to crashes.");
PyDoc_STRVAR(getrealref_doc, u8"getrealrefcount(obj)"
    u8"\n"
    u8"Get the actual reference count of an object before calling getrealrefcount(). Unlike "
    u8"sys.getrefcount(), this function ignores the reference count increase when called.\n"
    u8"获取调用本函数前对象的实际引用计数。和sys.getrefcount()不同，不考虑调用时新增的引用计数。");
PyDoc_STRVAR(setref_doc, u8"setrefcount(obj, n)"
    u8"\n"
    u8"Set the actual reference count of an object before calling setrefcount() to n, "
    u8"as a reverse of getrealrefcount(), ignoring the reference count increase when called.\n"
    u8"设置对象的实际引用计数(调用函数前)为n，和getrealrefcount()相反，不考虑调用时新增的引用计数。\n"
    u8"Warning:Improper use of this function may lead to crashes.");
PyDoc_STRVAR(list_in_doc, u8"list_in(obj, lst)"
    u8"\n"
    u8"判断obj是否在列表或元组lst中。\n与Python内置的obj in lst调用多次\"==\"运算符(__eq__)相比，"
    u8"本函数直接比较对象的指针，提高了效率。\n"
    u8"Determine whether `obj` is in the sequence `lst`.\nCompared to the built-in "
    u8"Python call `obj in lst` that invokes the `==` operator (__eq__) multiple times, "
    u8"this function directly compares the pointers to improve efficiency.");
PyDoc_STRVAR(getrefcount_nogil_doc, u8"getrefcount_nogil(obj)\n"
    u8"获取Python 3.14+ 无GIL版本的引用计数，返回一个元组，分别是(ob_ref_local, ob_ref_shared)，不考虑调用时新增的引用计数。\n"
    u8"Get the reference counts in GIL-free versions of Python 3.14+, returning a tuple of "
    u8"(ob_ref_local, ob_ref_shared), ignoring the reference count increase when called.");
PyDoc_STRVAR(setrefcount_nogil_doc, u8"setrefcount_nogil(obj,ref_data)\n"
    u8"设置Python 3.14+ 无GIL版本的引用计数，ref_data为(ob_ref_local, ob_ref_shared)的元组，不考虑调用时新增的引用计数。\n"
    u8"Set the reference counts in GIL-free versions of Python 3.14+, with ref_data being a tuple of "
    u8"(ob_ref_local, ob_ref_shared), ignoring the reference count increase when called.\n"
    u8"Warning:Improper use of this function may lead to crashes.");

#if PY_MAJOR_VERSION < 3
#error "Python 3 is required"
#endif

#if PY_MINOR_VERSION >= 14
#if defined(Py_GIL_DISABLED)
// _PY314_NO_GIL: 是否启用无GIL的引用计数功能
#define _PY314_NO_GIL
#endif

// 兼容旧版本Python
#elif PY_MINOR_VERSION <= 12
#define Py_mod_gil 0
#define Py_MOD_GIL_NOT_USED NULL

#if PY_MINOR_VERSION <= 11
#define Py_mod_multiple_interpreters 0
#define Py_MOD_PER_INTERPRETER_GIL_SUPPORTED NULL
#endif

#endif

static const int REFCNT_DELTA=2; // 调用时新增的引用计数
PyObject *convptr(PyObject *self, PyObject *args) {
    PyObject *obj = NULL;
    size_t num = 0;
    if (!PyArg_ParseTuple(args,((sizeof(void*)==8)?"K":"k"), &num)) { // 同时兼容32和64位
        return NULL;
    }

    obj = (PyObject*)num; // 获取指针对应的Python对象
    Py_INCREF(obj);
    return obj;
}
PyObject *py_incref(PyObject *self, PyObject *args) {
    PyObject *obj = NULL;
    if (!PyArg_ParseTuple(args, "O", &obj)) {
        return NULL;
    }

    Py_INCREF(obj);
    Py_RETURN_NONE;
}
PyObject *py_decref(PyObject *self, PyObject *args) {
    PyObject *obj = NULL;
    if (!PyArg_ParseTuple(args, "O", &obj)) {
        return NULL;
    }

    Py_DECREF(obj);
    Py_RETURN_NONE;
}

PyObject *getrealrefcount(PyObject *self, PyObject *args) {
#ifdef _PY314_NO_GIL
    PyErr_SetString(PyExc_NotImplementedError, "getrealrefcount is not available in GIL-free versions of Python 3.14+");
    return NULL;
#else
    PyObject *obj;
    if (!PyArg_ParseTuple(args,"O",&obj)){
        return NULL;
    }
    return PyLong_FromSsize_t(obj->ob_refcnt-REFCNT_DELTA);
#endif
}
PyObject *setrefcount(PyObject *self, PyObject *args, PyObject *kwargs) {
#ifdef _PY314_NO_GIL
    PyErr_SetString(PyExc_NotImplementedError, "setrefcount is not available in GIL-free versions of Python 3.14+");
    return NULL;
#else
    PyObject *obj;Py_ssize_t n;
    static char *keywords[]={"obj","n",NULL};
    if (!PyArg_ParseTupleAndKeywords(args,kwargs,"On",keywords,&obj,&n)){
        return NULL;
    }
    obj->ob_refcnt=n+REFCNT_DELTA; // 设置新引用计数
    Py_RETURN_NONE;
#endif
}
PyObject *getrefcount_nogil(PyObject *self, PyObject *args){
#ifndef _PY314_NO_GIL
    PyErr_SetString(PyExc_NotImplementedError, "getrefcount_nogil is only available in GIL-free versions of Python 3.14+");
    return NULL;
#else
    PyObject *obj;
    if (!PyArg_ParseTuple(args,"O",&obj)){
        return NULL;
    }
    PyObject *result = PyTuple_New(2);
    PyTuple_SetItem(result, 0, PyLong_FromUnsignedLong(obj->ob_ref_local-REFCNT_DELTA));
    PyTuple_SetItem(result, 1, PyLong_FromSize_t(obj->ob_ref_shared));
    return result;
#endif
}
PyObject *setrefcount_nogil(PyObject *self, PyObject *args, PyObject *kwargs){
#ifndef _PY314_NO_GIL
    PyErr_SetString(PyExc_NotImplementedError, "setrefcount_nogil is only available in GIL-free versions of Python 3.14+");
    return NULL;
#else
    PyObject *obj = NULL;
    PyObject *ref_data = NULL;
    static char *kwlist[] = {"obj", "ref_data", NULL};
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "OO", kwlist, &obj, &ref_data)) {
        return NULL;
    }
    if (!PyTuple_Check(ref_data) || PyTuple_Size(ref_data) != 2) {
        PyErr_SetString(PyExc_TypeError, "ref_data must be a tuple of (ob_ref_local, ob_ref_shared)");
        return NULL;
    }
    PyObject *ob_ref_local_obj = PyTuple_GetItem(ref_data, 0);
    PyObject *ob_ref_shared_obj = PyTuple_GetItem(ref_data, 1);

    uint32_t ob_ref_local = PyLong_AsUnsignedLong(ob_ref_local_obj)+REFCNT_DELTA;
    if (PyErr_Occurred()) return NULL;
    size_t ob_ref_shared = PyLong_AsSize_t(ob_ref_shared_obj);
    if (PyErr_Occurred()) return NULL;

    PyGILState_STATE gstate = PyGILState_Ensure();
    obj->ob_ref_local=ob_ref_local; // 设置新引用计数
    obj->ob_ref_shared=ob_ref_shared;
    PyGILState_Release(gstate);

    Py_RETURN_NONE;
#endif
}

PyObject *list_in(PyObject *self, PyObject *args, PyObject *kwargs) {
    PyObject *obj, *lst_obj;
    // 解析输入参数，参数为待查找对象和一个序列(列表或元组)
    static char *keywords[] = {"obj", "lst", NULL};
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "OO", keywords, &obj, &lst_obj)) {
        return NULL;
    }
    PyObject *lst = PySequence_Fast(lst_obj, "expect a sequence");
    Py_ssize_t n = PySequence_Fast_GET_SIZE(lst);
    PyObject *item;

    for (Py_ssize_t i = 0; i < n; ++i) {
        item = PySequence_Fast_GET_ITEM(lst, i);  // 获取索引i的元素
        if (obj == item) {
            Py_DECREF(lst);
            Py_RETURN_TRUE;
        }
    }

    Py_DECREF(lst);
    Py_RETURN_FALSE;
}
PyObject *_list_setnull(PyObject *self, PyObject *args) {
    PyObject *list;Py_ssize_t index;
    if (!PyArg_ParseTuple(args, "On", &list, &index)) return NULL;
    if (!PyList_Check(list)) {
        PyErr_SetString(PyExc_TypeError, "expected a list");
        return NULL;
    }

    if(PyList_SetItem(list, index, NULL) < 0) return NULL;
    Py_RETURN_NONE;
}

/*
 * List of functions to add to pyobj_extension in exec_pyobj_extension().
 */
static PyMethodDef pyobj_extension_functions[] = {
    { "convptr", (PyCFunction)convptr, METH_VARARGS, convptr_doc },
    { "py_incref", (PyCFunction)py_incref, METH_VARARGS, py_inc_doc },
    { "py_decref", (PyCFunction)py_decref, METH_VARARGS, py_dec_doc },
    { "getrealrefcount", (PyCFunction)getrealrefcount, METH_VARARGS, getrealref_doc },
    { "setrefcount", (PyCFunction)setrefcount, METH_VARARGS | METH_KEYWORDS, setref_doc },
    { "getrefcount_nogil", (PyCFunction)getrefcount_nogil, METH_VARARGS, getrefcount_nogil_doc },
    { "setrefcount_nogil", (PyCFunction)setrefcount_nogil, METH_VARARGS | METH_KEYWORDS, setrefcount_nogil_doc },
    { "list_in", (PyCFunction)list_in, METH_VARARGS | METH_KEYWORDS, list_in_doc },
    { "_list_setnull", (PyCFunction)_list_setnull, METH_VARARGS, "_list_setnull(lst,index)"},
    { NULL, NULL, 0, NULL } /* marks end of array */
};

/*
 * Initialize pyobj_extension. May be called multiple times, so avoid
 * using static state.
 */
int exec_pyobj_extension(PyObject *module) {
    PyModule_AddFunctions(module, pyobj_extension_functions);
    PyModule_AddStringConstant(module, "__author__", "qfcy");
    PyModule_AddStringConstant(module, "__version__", "1.2.6");
    PyModule_AddIntConstant(module, "_REFCNT_DELTA", REFCNT_DELTA);

    return 0; /* success */
}

/* Documentation for pyobj_extension. */
PyDoc_STRVAR(pyobj_extension_doc, u8"模块 pyobj_extension - pyobject库的C扩展模块, 提供一系列操作Python对象底层的函数。");

static PyModuleDef_Slot pyobj_extension_slots[] = {
    {Py_mod_exec, exec_pyobj_extension},
    {Py_mod_multiple_interpreters, Py_MOD_PER_INTERPRETER_GIL_SUPPORTED},
    {Py_mod_gil, Py_MOD_GIL_NOT_USED},
    {0, NULL}
};

static PyModuleDef pyobj_extension_def = {
    PyModuleDef_HEAD_INIT,
    "pyobj_extension",
    pyobj_extension_doc,
    0,              /* m_size */
    NULL,           /* m_methods */
    pyobj_extension_slots,
    NULL,           /* m_traverse */
    NULL,           /* m_clear */
    NULL,           /* m_free */
};

PyMODINIT_FUNC PyInit_pyobj_extension() {
    return PyModuleDef_Init(&pyobj_extension_def);
}
