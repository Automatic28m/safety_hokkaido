import re

# 1. Update layout.js
with open('src/app/[locale]/layout.js', 'r') as f:
    layout = f.read()

layout = layout.replace(
'''const torsilp = localFont({
  src: "../../fonts/TorsilpTontula.ttf",
  variable: "--font-torsilp",
});''',
'''const mittraphap = localFont({
  src: "../../fonts/FCMittraphap.ttf",
  variable: "--font-mittraphap",
});'''
)
layout = layout.replace('torsilp.variable', 'mittraphap.variable')

with open('src/app/[locale]/layout.js', 'w') as f:
    f.write(layout)

# 2. Update globals.css
with open('src/app/globals.css', 'r') as f:
    css = f.read()

css = css.replace('--font-torsilp: var(--font-torsilp);', '--font-mittraphap: var(--font-mittraphap);')

with open('src/app/globals.css', 'w') as f:
    f.write(css)
