import re

with open("src/components/ChatBot.jsx", "r") as f:
    content = f.read()

# Replace "Ready for answer" with "Ready for answer<br/><span className="text-xs opacity-75">Using AI model: gpt-oss-120b</span>"
# Or just "Ready for answer" -> "Ready for answer • Using AI model: gpt-oss-120b"

old_str = '<p className="text-white text-sm opacity-90 mt-0.5">Ready for answer</p>'
new_str = '<p className="text-white text-sm opacity-90 mt-0.5">Ready for answer <br/><span className="text-xs opacity-75">Using AI model: gpt-oss-120b</span></p>'

content = content.replace(old_str, new_str)

with open("src/components/ChatBot.jsx", "w") as f:
    f.write(content)
