"""MiMo secrets live in the OS credential store, never in project data."""
import ctypes
import os
import sys

SERVICE = 'Video Master / Xiaomi MiMo'
ACCOUNT = 'default'
ENV_NAMES = ('MIMO_API_KEY', 'XIAOMI_MIMO_API_KEY', 'XIAOMIMIMO_API_KEY')

class CredentialError(Exception): pass

def _mac_functions():
    sec = ctypes.CDLL('/System/Library/Frameworks/Security.framework/Security')
    core = ctypes.CDLL('/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation')
    vp, u32 = ctypes.c_void_p, ctypes.c_uint32
    sec.SecKeychainFindGenericPassword.argtypes = [vp,u32,ctypes.c_char_p,u32,ctypes.c_char_p,ctypes.POINTER(u32),ctypes.POINTER(vp),ctypes.POINTER(vp)]
    sec.SecKeychainFindGenericPassword.restype = ctypes.c_int32
    sec.SecKeychainAddGenericPassword.argtypes = [vp,u32,ctypes.c_char_p,u32,ctypes.c_char_p,u32,vp,ctypes.POINTER(vp)]
    sec.SecKeychainAddGenericPassword.restype = ctypes.c_int32
    sec.SecKeychainItemModifyAttributesAndData.argtypes = [vp,vp,u32,vp]
    sec.SecKeychainItemModifyAttributesAndData.restype = ctypes.c_int32
    sec.SecKeychainItemDelete.argtypes = [vp]; sec.SecKeychainItemDelete.restype = ctypes.c_int32
    sec.SecKeychainItemFreeContent.argtypes = [vp,vp]; sec.SecKeychainItemFreeContent.restype = ctypes.c_int32
    core.CFRelease.argtypes = [vp]
    return sec, core

def _mac_find():
    sec, core = _mac_functions(); service=SERVICE.encode(); account=ACCOUNT.encode()
    size=ctypes.c_uint32(); data=ctypes.c_void_p(); item=ctypes.c_void_p()
    code=sec.SecKeychainFindGenericPassword(None,len(service),service,len(account),account,ctypes.byref(size),ctypes.byref(data),ctypes.byref(item))
    if code == -25300: return sec,core,None,None
    if code != 0: raise CredentialError(f'无法访问 macOS 钥匙串（系统错误 {code}）')
    try: value=ctypes.string_at(data,size.value).decode('utf-8')
    finally: sec.SecKeychainItemFreeContent(None,data)
    return sec,core,item,value

def _mac_lookup():
    sec,core,item,value=_mac_find()
    if item: core.CFRelease(item)
    return value

def _mac_store(value):
    sec,core,item,_=_mac_find(); raw=value.encode('utf-8'); buffer=ctypes.create_string_buffer(raw); service=SERVICE.encode(); account=ACCOUNT.encode()
    try:
        if item: code=sec.SecKeychainItemModifyAttributesAndData(item,None,len(raw),buffer)
        else: code=sec.SecKeychainAddGenericPassword(None,len(service),service,len(account),account,len(raw),buffer,None)
        if code: raise CredentialError(f'无法保存到 macOS 钥匙串（系统错误 {code}）')
    finally:
        if item: core.CFRelease(item)

def _mac_delete():
    sec,core,item,_=_mac_find()
    if item:
        try:
            code=sec.SecKeychainItemDelete(item)
            if code: raise CredentialError(f'无法删除钥匙串项目（系统错误 {code}）')
        finally: core.CFRelease(item)

def _win_types():
    from ctypes import wintypes
    class Credential(ctypes.Structure):
        _fields_=[('Flags',wintypes.DWORD),('Type',wintypes.DWORD),('TargetName',wintypes.LPWSTR),('Comment',wintypes.LPWSTR),('LastWritten',wintypes.FILETIME),('CredentialBlobSize',wintypes.DWORD),('CredentialBlob',ctypes.POINTER(ctypes.c_ubyte)),('Persist',wintypes.DWORD),('AttributeCount',wintypes.DWORD),('Attributes',ctypes.c_void_p),('TargetAlias',wintypes.LPWSTR),('UserName',wintypes.LPWSTR)]
    lib=ctypes.WinDLL('Advapi32.dll',use_last_error=True)
    lib.CredReadW.argtypes=[wintypes.LPCWSTR,wintypes.DWORD,wintypes.DWORD,ctypes.POINTER(ctypes.POINTER(Credential))];lib.CredReadW.restype=wintypes.BOOL
    lib.CredWriteW.argtypes=[ctypes.POINTER(Credential),wintypes.DWORD];lib.CredWriteW.restype=wintypes.BOOL
    lib.CredDeleteW.argtypes=[wintypes.LPCWSTR,wintypes.DWORD,wintypes.DWORD];lib.CredDeleteW.restype=wintypes.BOOL
    lib.CredFree.argtypes=[ctypes.c_void_p]
    return lib,Credential

def _win_lookup():
    lib,Credential=_win_types(); item=ctypes.POINTER(Credential)()
    if not lib.CredReadW(SERVICE,1,0,ctypes.byref(item)):
        if ctypes.get_last_error()==1168:return None
        raise CredentialError(f'无法读取 Windows 凭据管理器（系统错误 {ctypes.get_last_error()}）')
    try:return ctypes.string_at(item.contents.CredentialBlob,item.contents.CredentialBlobSize).decode('utf-8')
    finally:lib.CredFree(item)

def _win_store(value):
    lib,Credential=_win_types(); raw=value.encode('utf-8'); buf=(ctypes.c_ubyte*len(raw)).from_buffer_copy(raw)
    item=Credential();item.Type=1;item.TargetName=SERVICE;item.UserName=ACCOUNT;item.CredentialBlobSize=len(raw);item.CredentialBlob=ctypes.cast(buf,ctypes.POINTER(ctypes.c_ubyte));item.Persist=2
    if not lib.CredWriteW(ctypes.byref(item),0):raise CredentialError(f'无法保存到 Windows 凭据管理器（系统错误 {ctypes.get_last_error()}）')

def _win_delete():
    lib,_=_win_types()
    if not lib.CredDeleteW(SERVICE,1,0) and ctypes.get_last_error()!=1168:raise CredentialError(f'无法删除 Windows 凭据（系统错误 {ctypes.get_last_error()}）')

def _lookup():
    if sys.platform=='darwin': return _mac_lookup()
    if sys.platform=='win32': return _win_lookup()
    return None

def _store(value):
    if sys.platform=='darwin':return _mac_store(value)
    if sys.platform=='win32':return _win_store(value)
    raise CredentialError('此系统暂不支持页面保存 Key；可在启动进程中设置 MIMO_API_KEY 环境变量。')

def _delete():
    if sys.platform=='darwin':return _mac_delete()
    if sys.platform=='win32':return _win_delete()
    raise CredentialError('此系统没有可删除的 Video Master 系统凭据。')

def store_name():
    return {'darwin':'macOS 钥匙串','win32':'Windows 凭据管理器'}.get(sys.platform,'进程环境变量')

def save_key(value):
    if not isinstance(value,str) or not value.strip() or len(value)>4096 or any(ord(c)<33 or ord(c)>126 for c in value): raise CredentialError('请输入有效的 API Key，不能包含空格或换行。')
    _store(value)

def delete_key(): _delete()

def environment_key():
    return next((os.environ[name] for name in ENV_NAMES if os.environ.get(name)), None)

def load_key(): return _lookup() or environment_key()

def status():
    saved=_lookup()
    source='system' if saved else ('environment' if environment_key() else 'none')
    return {'configured':source!='none','source':source,'storage':store_name()}
