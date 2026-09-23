import re

with open('src/app/[locale]/layout.js', 'r') as f:
    content = f.read()

content = content.replace('<FloatingButtons />', '<div className="animate-fade-in opacity-0" style={{ animationDelay: "500ms" }}><FloatingButtons /></div>')

with open('src/app/[locale]/layout.js', 'w') as f:
    f.write(content)
