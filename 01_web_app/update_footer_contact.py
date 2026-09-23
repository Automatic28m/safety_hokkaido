import re

with open('src/components/Footer.jsx', 'r') as f:
    content = f.read()

# Replace mobile copyright block
mobile_copyright = """          <div className="mt-12 text-center text-sm opacity-80 flex flex-col items-center gap-2">
            <div>Contact: <a href="mailto:phanlop.auto@gmail.com" className="hover:text-orange-300 transition-colors hover:underline">phanlop.auto@gmail.com</a></div>
            <div>©2026 SafetyHokaido.</div>
          </div>"""
content = re.sub(r'<div className="mt-12 text-center text-sm opacity-80">\s*©2026 SafetyHokaido.\s*</div>', mobile_copyright, content)

# Replace desktop copyright block (note the double k in Hokkaido in the original desktop block)
desktop_copyright = """          <div className="mt-16 text-center text-sm opacity-80 flex flex-col items-center gap-2">
            <div>Contact: <a href="mailto:phanlop.auto@gmail.com" className="hover:text-orange-300 transition-colors hover:underline">phanlop.auto@gmail.com</a></div>
            <div>©2026 SafetyHokkaido.</div>
          </div>"""
content = re.sub(r'<div className="mt-16 text-center text-sm opacity-80">\s*©2026 SafetyHokkaido.\s*</div>', desktop_copyright, content)

with open('src/components/Footer.jsx', 'w') as out_f:
    out_f.write(content)
