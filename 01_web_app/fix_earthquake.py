import re

with open('src/app/[locale]/disaster/earthquake/page.jsx', 'r') as f:
    content = f.read()

# I will write a simple python script to cleanly rewrite the return block of Earthquake page.
# Actually I'll just write the entire page out, it's not too long and much safer than trying to regex match a broken react tree.
