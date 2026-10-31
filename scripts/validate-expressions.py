#!/usr/bin/env python3
"""校验 expressions/packs。build.py 会再跑一遍，失败则构建中断。"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import expr

def main():
    root = sys.argv[1] if len(sys.argv) > 1 else expr.ROOT
    packs = expr.load_packs(root)
    n = sum(len(p['items']) for p in packs)
    gated = [p['id'] for p in packs if p['gated']]
    print('通过：%d 个包，%d 条' % (len(packs), n) + ('，年龄门槛：%s' % '、'.join(gated) if gated else ''))

if __name__ == '__main__':
    main()
