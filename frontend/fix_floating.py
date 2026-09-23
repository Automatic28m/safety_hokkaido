import re

with open('src/components/FloatingButtons.jsx', 'r') as f:
    content = f.read()

# Replace the Link and button classes for the floating items
content = content.replace(
    'className="relative group transition-transform hover:scale-105 flex flex-col items-center"',
    'className="relative group transition-all duration-300 hover:scale-110 hover:-translate-y-2 hover:drop-shadow-2xl flex flex-col items-center"'
)

# Also increase the shadow on the inner div
content = content.replace(
    'shadow-lg border-[3px]',
    'shadow-xl shadow-black/40 border-[3px]'
)

with open('src/components/FloatingButtons.jsx', 'w') as out_f:
    out_f.write(content)
