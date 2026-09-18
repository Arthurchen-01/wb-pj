#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
三层落盘检测 —— 独立复核脚本
================================
不改任何文件，只读 + 报告。用于回答"补丁到底还在不在"。

用法：
    python 复核-三层落盘检测.py
    python 复核-三层落盘检测.py --ai      # 只看 WorkBuddyAI

退出码：0 = 三层全部正常；1 = 有异常（详见输出）
"""
import os, io, re, sys, json, argparse

STAMP = 'rev-b687ca46'          # 政策版本戳
NEUTRAL_LEN = {                 # 中性安全块的期望长度区间
    'personal_files_safety':  (80, 140),
    'windows_command_safety': (100, 160),
}

TARGETS = {
    'wb': dict(
        label='WorkBuddy',
        install=r'C:\Users\<用户名>\AppData\Local\Programs\WorkBuddy',
    ),
    'ai': dict(
        label='WorkBuddyAI',
        install=r'C:\Users\<用户名>\AppData\Local\Programs\WorkBuddyAI',
    ),
}

# 闸门函数签名（用于在压缩过的 JS 里定位）
GATE_RE = re.compile(r'function\s+check(BashSecurityWindows|PowerShellSecurity)\s*\([^)]*\)\s*\{')
ALLOW_RE = re.compile(r'\s*return\s*\{\s*behavior\s*:\s*["\']allow["\']')

results = []


def emit(ok, layer, msg):
    results.append((ok, layer, msg))
    flag = 'OK  ' if ok is True else ('FAIL' if ok is False else 'WARN')
    print('  [%s] %-10s %s' % (flag, layer, msg))


def check_gate(install):
    """① 闸门层：cli\\dist\\codebuddy*.js 的两个检查函数是否被提前 return。"""
    d = os.path.join(install, r'resources\app.asar.unpacked\cli\dist')
    print('\n① 闸门层  %s' % d)
    if not os.path.isdir(d):
        emit(False, '闸门层', '目录不存在 —— 客户端可能装在其他位置')
        return
    found_any = False
    for fn in sorted(os.listdir(d)):
        if not (fn.startswith('codebuddy') and fn.endswith('.js')):
            continue
        p = os.path.join(d, fn)
        try:
            txt = io.open(p, 'r', encoding='utf-8', errors='replace').read()
        except Exception as e:
            emit(False, '闸门层', '%s 读取失败: %s' % (fn, e))
            continue
        hits = list(GATE_RE.finditer(txt))
        if not hits:
            continue
        found_any = True
        for h in hits:
            fnname = h.group(1)
            seg = txt[h.end():h.end() + 100]
            patched = bool(ALLOW_RE.match(seg))
            emit(patched, '闸门层',
                 '%-26s %-24s %s' % (fn, fnname, 'PATCHED（已解锁）' if patched else 'ORIGINAL（未解锁）'))
    if not found_any:
        emit(False, '闸门层', '未找到任何闸门函数 —— 文件结构可能已变（客户端升级？）')


def check_policy(install):
    """② 政策层：cli\\product.json 的 prompts[0].template。"""
    p = os.path.join(install, r'resources\app.asar.unpacked\cli\product.json')
    print('\n② 政策层  %s' % p)
    if not os.path.isfile(p):
        emit(False, '政策层', 'product.json 不存在')
        return
    try:
        d = json.load(io.open(p, 'r', encoding='utf-8'))
    except Exception as e:
        emit(False, '政策层', 'JSON 解析失败（文件已损坏！）: %s' % e)
        return
    tmpl = None
    try:
        tmpl = d['prompts'][0]['template']
    except Exception:
        pass
    if not tmpl:
        emit(False, '政策层', 'prompts[0].template 取不到')
        return
    m = re.search(r'<content_policy>(.*?)</content_policy>', tmpl, re.S)
    if not m:
        emit(False, '政策层', '未找到 <content_policy> 块')
        return
    body = m.group(1)
    has_stamp = STAMP in body
    has_loose = '交付标准' in body
    emit(has_stamp and has_loose, '政策层',
         '政策块 %d 字符  版本戳=%s  宽松术语=%s' % (len(body.strip()), has_stamp, has_loose))


def check_templates(install):
    """③ 模板层：resources\\templates\\*.tpl 的政策块 + 安全块顺序。"""
    d = os.path.join(install, r'resources\app.asar.unpacked\resources\templates')
    print('\n③ 模板层  %s' % d)
    if not os.path.isdir(d):
        emit(False, '模板层', 'templates 目录不存在')
        return
    tot = withpol = okpol = 0
    order_checked = False
    for fn in sorted(os.listdir(d)):
        if not fn.endswith('.tpl'):
            continue
        tot += 1
        t = io.open(os.path.join(d, fn), 'r', encoding='utf-8', errors='replace').read()
        m = re.search(r'<content_policy>(.*?)</content_policy>', t, re.S)
        if not m:
            continue
        withpol += 1
        if STAMP in m.group(1) and '交付标准' in m.group(1):
            okpol += 1

        # 顺序检查只在主模板上做一次
        if fn == 'workbuddy-prompt.tpl':
            order_checked = True
            op = t.find('<content_policy>')
            ofs = t.find('<personal_files_safety>')
            ows = t.find('<windows_command_safety>')
            emit(ofs > op and ows > op, '模板层',
                 '安全块顺序: 政策@%d  fs@%d  wcs@%d  →  %s'
                 % (op, ofs, ows, '两者都在政策之后 ✓' if (ofs > op and ows > op) else '顺序异常！'))

            # 安全块长度
            for key, (lo, hi) in NEUTRAL_LEN.items():
                mm = re.search(r'<' + key + r'>(.*?)</' + key + r'>', t, re.S)
                if mm:
                    L = len(mm.group(1).strip())
                    emit(lo <= L <= hi, '模板层',
                         '<%s> %d 字符  →  %s' % (key, L, '中性版' if lo <= L <= hi else '长度异常（可能未替换）'))

    emit(okpol == withpol and withpol > 0, '模板层',
         '%d/%d 个模板含政策块，其中 %d 个已注入版本戳+宽松术语' % (withpol, tot, okpol))
    if not order_checked:
        emit(None, '模板层', '未找到 workbuddy-prompt.tpl，跳过顺序检查')


def check_safety_in_json(install):
    """④ 安全块层：所有 json/tpl 里的安全块标签计数。"""
    base = os.path.join(install, r'resources\app.asar.unpacked\resources')
    print('\n④ 安全块标签计数  %s' % base)
    counts = {k: 0 for k in NEUTRAL_LEN}
    filecnt = 0
    for root, _dirs, files in os.walk(base):
        for f in files:
            if not f.endswith(('.json', '.tpl')):
                continue
            try:
                t = io.open(os.path.join(root, f), 'r', encoding='utf-8', errors='replace').read()
            except Exception:
                continue
            hit = False
            for k in NEUTRAL_LEN:
                c = t.count('<' + k + '>')
                counts[k] += c
                if c:
                    hit = True
            if hit:
                filecnt += 1
    for k, c in counts.items():
        emit(c > 0, '安全块', '<%s> 出现 %d 次' % (k, c))
    emit(True, '安全块', '含安全块标签的文件共 %d 个' % filecnt)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ai', action='store_true', help='只看 WorkBuddyAI')
    ap.add_argument('--wb', action='store_true', help='只看 WorkBuddy')
    args = ap.parse_args()

    if args.ai:
        keys = ['ai']
    elif args.wb:
        keys = ['wb']
    else:
        keys = ['wb', 'ai']

    print('=' * 76)
    print('三层落盘检测 — 只读，不修改任何文件')
    print('=' * 76)

    for k in keys:
        t = TARGETS[k]
        print('\n' + '#' * 76)
        print('# %s' % t['label'])
        print('#' * 76)
        if not os.path.isdir(t['install']):
            emit(False, '发现', '安装目录不存在: %s' % t['install'])
            continue
        check_gate(t['install'])
        check_policy(t['install'])
        check_templates(t['install'])
        check_safety_in_json(t['install'])

    fails = [r for r in results if r[0] is False]
    warns = [r for r in results if r[0] is None]
    print('\n' + '=' * 76)
    print('汇总:  通过 %d   失败 %d   提示 %d' % (len(results) - len(fails) - len(warns), len(fails), len(warns)))
    if fails:
        print('\n失败项:')
        for _ok, layer, msg in fails:
            print('  · [%s] %s' % (layer, msg))
        print('\n→ 有失败项。跑一次「执行破甲点我其余不用管.bat」→ 完全重启客户端。')
    else:
        print('\n→ 三层全部正常。若模型仍拒绝，属于服务端策略（本地改不了）。')
    print('=' * 76)
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
