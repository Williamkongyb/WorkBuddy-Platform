# -*- coding: utf-8 -*-
"""
Windows GBK 控制台安全打印模块
解决 emoji 等非 GBK 字符导致的 UnicodeEncodeError
"""
import sys
import re

_EMOJI_RE = re.compile(r'[\U0001F000-\U0001FFFF]')

# 记住原始的 print 函数
_original_print = print


def safe_print(*args, **kwargs):
    """安全打印，自动处理 emoji 编码问题，回退到纯文本"""
    text_parts = []
    for a in args:
        if isinstance(a, str):
            text_parts.append(_EMOJI_RE.sub('', a))
        else:
            text_parts.append(str(a))

    try:
        _original_print(*text_parts, **kwargs)
    except UnicodeEncodeError:
        ascii_parts = []
        for p in text_parts:
            try:
                p.encode('ascii')
                ascii_parts.append(p)
            except UnicodeEncodeError:
                ascii_parts.append(p.encode('ascii', errors='replace').decode('ascii'))
        try:
            _original_print(*ascii_parts, **kwargs)
        except Exception:
            _original_print("(print encoding error - suppressed)", **kwargs)
