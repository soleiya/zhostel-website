#!/usr/bin/env python3
"""The striped Z logo PNG has a transparent Z: give it a white backing so the Z reads white on any photo."""
c = "assets/css/site.css"
css = open(c, encoding="utf-8").read()
old = ".hero .logo--brand { border-radius: 50%; box-shadow: 0 6px 24px rgba(0,0,0,.35); }"
assert old in css, "logo rule not found"
css = css.replace(old, ".hero .logo--brand { border-radius: 50%; background: #fff; box-shadow: 0 6px 24px rgba(0,0,0,.35); }")
open(c, "w", encoding="utf-8").write(css)
print("logo fixed")
