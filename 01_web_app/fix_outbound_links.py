import re

def replace_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

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
    # Wait, bus link2 is JR Hokkaido Bus
    if "bus/page.jsx" in filepath:
        content = re.sub(
            r'<Link href={`/\${locale}/learning-materials`}([^>]*?{t\(\'link2Title\'\)}.*?)<\/Link>',
            r'<a href="https://www.jrhokkaidobus.com/en/" target="_blank" rel="noopener noreferrer"\1</a>',
            content, flags=re.DOTALL
        )
    # The first one was already replaced by the generic replacement if it was Hokkaido District Transport Bureau
    # Wait, my first replacement has `([^>]*?Hokkaido District Transport Bureau.*?)<\/Link>` which works for bus too.

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

    with open(filepath, 'w') as f:
        f.write(content)

files = [
    'src/app/[locale]/transportation/train/page.jsx',
    'src/app/[locale]/transportation/bus/page.jsx',
    'src/app/[locale]/transportation/car/page.jsx',
    'src/app/[locale]/learning-materials/page.jsx',
    'src/app/[locale]/emergency-contact/page.jsx',
    'src/app/[locale]/disaster/earthquake/page.jsx',
]

for f in files:
    try:
        replace_file(f)
    except Exception as e:
        print(f"Failed {f}: {e}")

