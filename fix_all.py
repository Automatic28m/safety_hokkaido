import re

files = [
    'src/app/[locale]/transportation/train/page.jsx',
    'src/app/[locale]/transportation/bus/page.jsx',
    'src/app/[locale]/transportation/car/page.jsx',
    'src/app/[locale]/learning-materials/page.jsx',
    'src/app/[locale]/emergency-contact/page.jsx',
    'src/app/[locale]/disaster/earthquake/page.jsx',
]

def replace_links(content, filepath):
    # Train
    content = re.sub(
        r'<Link href={`/\${locale}/learning-materials`}([^>]*?Hokkaido District Transport Bureau.*?)<\/Link>',
        r'<a href="https://wwwtb.mlit.go.jp/hokkaido/unkoujouhou/index.html" target="_blank" rel="noopener noreferrer"\1</a>',
        content, flags=re.DOTALL
    )
    content = re.sub(
        r'<Link href={`/\${locale}/learning-materials`}([^>]*?{t\(\'link2Title\'\)}.*?)<\/Link>',
        r'<a href="https://www.jrhokkaido.co.jp/global/index.html" target="_blank" rel="noopener noreferrer"\1</a>',
        content, flags=re.DOTALL
    )
    
    # Bus
    if "bus/page.jsx" in filepath:
        content = re.sub(
            r'<Link href={`/\${locale}/learning-materials`}([^>]*?{t\(\'link2Title\'\)}.*?)<\/Link>',
            r'<a href="https://www.jrhokkaidobus.com/en/" target="_blank" rel="noopener noreferrer"\1</a>',
            content, flags=re.DOTALL
        )

    # Car
    if "car/page.jsx" in filepath:
        content = re.sub(
            r'<Link href={`/\${locale}/learning-materials`}([^>]*?{t\(\'linkTitle\'\)}.*?)<\/Link>',
            r'<a href="https://wwwtb.mlit.go.jp/hokkaido/unkoujouhou/index.html" target="_blank" rel="noopener noreferrer"\1</a>',
            content, flags=re.DOTALL
        )

    # Emergency Contact / Learning Materials
    content = re.sub(
        r'<Link href={`/\${locale}/learning-materials`}([^>]*?{t\(\'link1Title\'\)}.*?)<\/Link>',
        r'<a href="https://www.japan.travel/en/plan/hotline/" target="_blank" rel="noopener noreferrer"\1</a>',
        content, flags=re.DOTALL
    )
    content = re.sub(
        r'<Link href={`/\${locale}/learning-materials`}([^>]*?{t\(\'link2Title\'\)}.*?)<\/Link>',
        r'<a href="https://www.japan.travel/en/news/JapanSafeTravel/" target="_blank" rel="noopener noreferrer"\1</a>',
        content, flags=re.DOTALL
    )
    content = re.sub(
        r'<Link href={`/\${locale}/learning-materials`}([^>]*?{t\(\'link3Title\'\)}.*?)<\/Link>',
        r'<a href="https://crisis.yahoo.co.jp/map/" target="_blank" rel="noopener noreferrer"\1</a>',
        content, flags=re.DOTALL
    )
    
    # Earthquake (link1Title is Evacuation Shelter Map)
    if "earthquake/page.jsx" in filepath:
        content = re.sub(
            r'<Link href={`/\${locale}/learning-materials`}([^>]*?{t\(\'link1Title\'\)}.*?)<\/Link>',
            r'<a href="https://crisis.yahoo.co.jp/map/" target="_blank" rel="noopener noreferrer"\1</a>',
            content, flags=re.DOTALL
        )
    return content


for filepath in files:
    with open(filepath, 'r') as f:
        content = f.read()

    content = replace_links(content, filepath)
    content = content.replace("bg-green-500", "bg-green-700").replace("text-green-500", "text-green-700")

    with open(filepath, 'w') as f:
        f.write(content)
