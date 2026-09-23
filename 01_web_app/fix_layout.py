import re

with open('src/app/[locale]/layout.js', 'r') as f:
    content = f.read()

# Add animate-fade-in to Navbar
content = content.replace('<Navbar />', '<div className="animate-fade-in opacity-0" style={{ animationDelay: "100ms" }}><Navbar /></div>')

# Add animate-fade-in to Footer
content = content.replace('<Footer />', '<div className="animate-fade-in opacity-0" style={{ animationDelay: "300ms" }}><Footer /></div>')

with open('src/app/[locale]/layout.js', 'w') as f:
    f.write(content)
