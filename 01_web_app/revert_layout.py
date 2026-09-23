import re

with open('src/app/[locale]/layout.js', 'r') as f:
    content = f.read()

# Remove the wrappers
content = content.replace('<div className="animate-fade-in opacity-0" style={{ animationDelay: "100ms" }}><Navbar /></div>', '<Navbar />')
content = content.replace('<div className="animate-fade-in opacity-0" style={{ animationDelay: "300ms" }}><Footer /></div>', '<Footer />')
content = content.replace('<div className="animate-fade-in opacity-0" style={{ animationDelay: "500ms" }}><FloatingButtons /></div>', '<FloatingButtons />')

with open('src/app/[locale]/layout.js', 'w') as f:
    f.write(content)
