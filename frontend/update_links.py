import os
import re

# We will replace Link hrefs with standard anchor tags for outbound links

files = [
    'src/app/[locale]/transportation/train/page.jsx',
    'src/app/[locale]/transportation/bus/page.jsx',
    'src/app/[locale]/transportation/car/page.jsx',
    'src/app/[locale]/learning-materials/page.jsx',
    'src/app/[locale]/emergency-contact/page.jsx',
    'src/app/[locale]/disaster/earthquake/page.jsx',
]

def replace_in_file(filepath, replacements):
    if not os.path.exists(filepath): return
    with open(filepath, 'r') as f:
        content = f.read()
    
    for old, new in replacements:
        content = content.replace(old, new)
        
    with open(filepath, 'w') as f:
        f.write(content)


for filepath in files:
    if not os.path.exists(filepath): continue
    with open(filepath, 'r') as f:
        content = f.read()

    # 1. Hokkaido District Transport Bureau (Used in Train, Bus, Car)
    content = re.sub(
        r'<Link href={`/\${locale}/learning-materials`} className="bg-white rounded-2xl p-6 shadow-md flex items-center justify-between group hover:shadow-lg transition-shadow">(\s*<div>\s*<div className="flex items-center gap-2 mb-2">\s*<div className="w-3 h-3 rounded-full bg-green-700 shrink-0"></div>\s*<h3 className="text-lg font-bold text-black leading-tight">(?:Hokkaido District Transport Bureau|{t\(\'linkTitle\'\)})</h3>)',
        r'<a href="https://wwwtb.mlit.go.jp/hokkaido/unkoujouhou/index.html" target="_blank" rel="noopener noreferrer" className="bg-white rounded-2xl p-6 shadow-md flex items-center justify-between group hover:shadow-lg transition-shadow">\1',
        content
    )

    # 2. HOKKAIDO RAILWAY COMPANY (Used in Train)
    content = re.sub(
        r'<Link href={`/\${locale}/learning-materials`} className="bg-white rounded-2xl p-6 shadow-md flex items-center justify-between group hover:shadow-lg transition-shadow">(\s*<div>\s*<div className="flex items-center gap-2 mb-2">\s*<div className="w-3 h-3 rounded-full bg-green-700 shrink-0"></div>\s*<h3 className="text-lg font-bold text-black leading-tight">{t\(\'link2Title\'\)}</h3>)',
        r'<a href="https://www.jrhokkaido.co.jp/global/index.html" target="_blank" rel="noopener noreferrer" className="bg-white rounded-2xl p-6 shadow-md flex items-center justify-between group hover:shadow-lg transition-shadow">\1',
        content
    )

    # 3. JR Hokkaido Bus (Used in Bus)
    content = re.sub(
        r'<Link href={`/\${locale}/learning-materials`} className="bg-white rounded-2xl p-6 shadow-md flex items-center justify-between group hover:shadow-lg transition-shadow">(\s*<div>\s*<div className="flex items-center gap-2 mb-2">\s*<div className="w-3 h-3 rounded-full bg-green-700 shrink-0"></div>\s*<h3 className="text-lg font-bold text-black leading-tight">{t\(\'link2Title\'\)}</h3>)',
        r'<a href="https://www.jrhokkaidobus.com/en/" target="_blank" rel="noopener noreferrer" className="bg-white rounded-2xl p-6 shadow-md flex items-center justify-between group hover:shadow-lg transition-shadow">\1',
        content
    )

    # 4. Japan Visitor Hotline (Used in Learning Materials, Emergency Contact)
    content = re.sub(
        r'<Link href={`/\${locale}/learning-materials`} className="bg-white rounded-2xl p-6 shadow-md flex items-center justify-between group hover:shadow-lg transition-shadow">(\s*<div>\s*<div className="flex items-center gap-2 mb-2">\s*<div className="w-3 h-3 rounded-full bg-green-700 shrink-0 mt-1.5"></div>\s*<h3 className="text-lg font-bold text-black leading-tight">{t\(\'link1Title\'\)}</h3>)',
        r'<a href="https://www.japan.travel/en/plan/hotline/" target="_blank" rel="noopener noreferrer" className="bg-white rounded-2xl p-6 shadow-md flex items-center justify-between group hover:shadow-lg transition-shadow">\1',
        content
    )
    content = re.sub(
        r'<Link href={`/\${locale}/learning-materials`} className="bg-white rounded-2xl p-4 md:p-6 shadow-md flex items-center justify-between group hover:shadow-lg transition-shadow">(\s*<div>\s*<div className="flex items-center gap-2 mb-2">\s*<div className="hidden md:block w-3 h-3 rounded-full bg-green-700 shrink-0"></div>\s*<h3 className="text-base md:text-lg font-bold text-black leading-tight">{t\(\'link1Title\'\)}</h3>)',
        r'<a href="https://www.japan.travel/en/plan/hotline/" target="_blank" rel="noopener noreferrer" className="bg-white rounded-2xl p-4 md:p-6 shadow-md flex items-center justify-between group hover:shadow-lg transition-shadow">\1',
        content
    )

    # 5. JNTO – Japan Safe Travel (Used in Learning Materials, Emergency Contact)
    content = re.sub(
        r'<Link href={`/\${locale}/learning-materials`} className="bg-white rounded-2xl p-6 shadow-md flex items-center justify-between group hover:shadow-lg transition-shadow">(\s*<div>\s*<div className="flex items-center gap-2 mb-2">\s*<div className="w-3 h-3 rounded-full bg-green-700 shrink-0 mt-1.5"></div>\s*<h3 className="text-lg font-bold text-black leading-tight">{t\(\'link2Title\'\)}</h3>)',
        r'<a href="https://www.japan.travel/en/news/JapanSafeTravel/" target="_blank" rel="noopener noreferrer" className="bg-white rounded-2xl p-6 shadow-md flex items-center justify-between group hover:shadow-lg transition-shadow">\1',
        content
    )
    content = re.sub(
        r'<Link href={`/\${locale}/learning-materials`} className="bg-white rounded-2xl p-4 md:p-6 shadow-md flex items-center justify-between group hover:shadow-lg transition-shadow">(\s*<div>\s*<div className="flex items-center gap-2 mb-2">\s*<div className="hidden md:block w-3 h-3 rounded-full bg-green-700 shrink-0"></div>\s*<h3 className="text-base md:text-lg font-bold text-black leading-tight">{t\(\'link2Title\'\)}</h3>)',
        r'<a href="https://www.japan.travel/en/news/JapanSafeTravel/" target="_blank" rel="noopener noreferrer" className="bg-white rounded-2xl p-4 md:p-6 shadow-md flex items-center justify-between group hover:shadow-lg transition-shadow">\1',
        content
    )

    # 6. Evacuation Shelter Map (Used in Learning Materials, Emergency Contact, Earthquake)
    content = re.sub(
        r'<Link href={`/\${locale}/learning-materials`} className="bg-white rounded-2xl p-6 shadow-md flex items-center justify-between group hover:shadow-lg transition-shadow">(\s*<div>\s*<div className="flex items-center gap-2 mb-2">\s*<div className="w-3 h-3 rounded-full bg-green-700 shrink-0 mt-1.5"></div>\s*<h3 className="text-lg font-bold text-black leading-tight">{t\(\'link3Title\'\)}</h3>)',
        r'<a href="https://crisis.yahoo.co.jp/map/" target="_blank" rel="noopener noreferrer" className="bg-white rounded-2xl p-6 shadow-md flex items-center justify-between group hover:shadow-lg transition-shadow">\1',
        content
    )
    content = re.sub(
        r'<Link href={`/\${locale}/learning-materials`} className="bg-white rounded-2xl p-4 md:p-6 shadow-md flex items-center justify-between group hover:shadow-lg transition-shadow">(\s*<div>\s*<div className="flex items-center gap-2 mb-2">\s*<div className="hidden md:block w-3 h-3 rounded-full bg-green-700 shrink-0"></div>\s*<h3 className="text-base md:text-lg font-bold text-black leading-tight">{t\(\'link3Title\'\)}</h3>)',
        r'<a href="https://crisis.yahoo.co.jp/map/" target="_blank" rel="noopener noreferrer" className="bg-white rounded-2xl p-4 md:p-6 shadow-md flex items-center justify-between group hover:shadow-lg transition-shadow">\1',
        content
    )
    content = re.sub(
        r'<Link href={`/\${locale}/learning-materials`} className="bg-white rounded-2xl p-6 shadow-md flex items-center justify-between group hover:shadow-lg transition-shadow">(\s*<div>\s*<div className="flex items-center gap-2 mb-2">\s*<div className="w-3 h-3 rounded-full bg-green-700"></div>\s*<h4 className="text-lg font-bold text-black leading-tight">{t\(\'link1Title\'\)}</h4>)',
        r'<a href="https://crisis.yahoo.co.jp/map/" target="_blank" rel="noopener noreferrer" className="bg-white rounded-2xl p-6 shadow-md flex items-center justify-between group hover:shadow-lg transition-shadow">\1',
        content
    )

    # Finally replace the closing </Link> with </a> for any of the above replacements
    # A bit hacky, let's just do a regex replace if the open tag is <a>
    # Actually, the safest way is to do it properly. Let's fix closing tags for everything we just touched.
    # We can rely on the fact that if it has <a href=... we need to replace the next </Link> with </a>
    # Let's do it with a loop or regex
    
    with open(filepath, 'w') as f:
        f.write(content)

