import re

with open('src/components/Footer.jsx', 'r') as f:
    content = f.read()

# Replace Mobile layout topics with details/summary accordions
mobile_disaster = """            <details className="group cursor-pointer">
              <summary className="font-bold text-lg mb-2 list-none hover:text-orange-300 transition-colors flex justify-between items-center [&::-webkit-details-marker]:hidden">
                Disaster
                <svg className="w-5 h-5 transition-transform group-open:rotate-180" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
              </summary>
              <ul className="pl-6 space-y-2 opacity-90 text-[15px] pb-4">
                <li className="transition-transform hover:translate-x-2"><Link href={`/${locale}/disaster/blizzard`} className="block w-full">Blizzard</Link></li>
                <li className="transition-transform hover:translate-x-2"><Link href={`/${locale}/disaster/earthquake`} className="block w-full">Earthquake</Link></li>
              </ul>
            </details>"""
content = re.sub(r'<div>\s*<h3 className="font-bold text-lg mb-2">Disaster</h3>\s*<ul className="pl-6 space-y-2 opacity-90 text-\[15px\]">\s*<li>.*?Blizzard.*?</li>\s*<li>.*?Earthquake.*?</li>\s*</ul>\s*</div>', mobile_disaster, content, flags=re.DOTALL)

mobile_transportation = """            <details className="group cursor-pointer">
              <summary className="font-bold text-lg mb-2 list-none hover:text-orange-300 transition-colors flex justify-between items-center [&::-webkit-details-marker]:hidden">
                Transportation
                <svg className="w-5 h-5 transition-transform group-open:rotate-180" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
              </summary>
              <ul className="pl-6 space-y-2 opacity-90 text-[15px] pb-4">
                <li className="transition-transform hover:translate-x-2"><Link href={`/${locale}/transportation/train`} className="block w-full">Train</Link></li>
                <li className="transition-transform hover:translate-x-2"><Link href={`/${locale}/transportation/bus`} className="block w-full">Bus</Link></li>
                <li className="transition-transform hover:translate-x-2"><Link href={`/${locale}/transportation/car`} className="block w-full">Rental Car</Link></li>
              </ul>
            </details>"""
content = re.sub(r'<div>\s*<h3 className="font-bold text-lg mb-2">Transportation</h3>\s*<ul className="pl-6 space-y-2 opacity-90 text-\[15px\]">\s*<li>.*?Train.*?</li>\s*<li>.*?Bus.*?</li>\s*<li>.*?Rental Car.*?</li>\s*</ul>\s*</div>', mobile_transportation, content, flags=re.DOTALL)

mobile_learning = """            <details className="group cursor-pointer">
              <summary className="font-bold text-lg mb-2 list-none hover:text-orange-300 transition-colors flex justify-between items-center [&::-webkit-details-marker]:hidden">
                Learning Materials
                <svg className="w-5 h-5 transition-transform group-open:rotate-180" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
              </summary>
              <ul className="pl-6 space-y-2 opacity-90 text-[15px] pb-4">
                <li className="transition-transform hover:translate-x-2"><Link href={`/${locale}/learning-materials#alerts`} className="block w-full">About Alerts</Link></li>
                <li className="transition-transform hover:translate-x-2"><Link href={`/${locale}/learning-materials#power-outages`} className="block w-full">Power outages</Link></li>
                <li className="transition-transform hover:translate-x-2"><Link href={`/${locale}/learning-materials#links`} className="block w-full">Links</Link></li>
              </ul>
            </details>"""
content = re.sub(r'<div>\s*<h3 className="font-bold text-lg mb-2">Learning Materials</h3>\s*<ul className="pl-6 space-y-2 opacity-90 text-\[15px\]">\s*<li>.*?About Alerts.*?</li>\s*<li>.*?Power outages.*?</li>\s*<li>.*?Links.*?</li>\s*</ul>\s*</div>', mobile_learning, content, flags=re.DOTALL)


# Desktop replacements (using open by default so layout doesn't completely collapse awkwardly)
desktop_disaster = """                <details open className="group cursor-pointer">
                  <summary className="font-bold text-base mb-3 list-none hover:text-orange-300 transition-colors flex justify-between items-center pr-4 [&::-webkit-details-marker]:hidden">
                    Disaster
                    <svg className="w-4 h-4 transition-transform group-open:rotate-180" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
                  </summary>
                  <ul className="pl-0 space-y-2 opacity-80 text-sm overflow-hidden transition-all">
                    <li className="transition-transform hover:translate-x-2"><Link href={`/${locale}/disaster/blizzard`} className="hover:underline block w-full">Blizzard</Link></li>
                    <li className="transition-transform hover:translate-x-2"><Link href={`/${locale}/disaster/earthquake`} className="hover:underline block w-full">Earthquake</Link></li>
                  </ul>
                </details>"""
content = re.sub(r'<div>\s*<h3 className="font-bold text-base mb-3">Disaster</h3>\s*<ul className="pl-0 space-y-2 opacity-80 text-sm">\s*<li>.*?Blizzard.*?</li>\s*<li>.*?Earthquake.*?</li>\s*</ul>\s*</div>', desktop_disaster, content, flags=re.DOTALL)


desktop_trans = """              <details open className="flex flex-col group cursor-pointer w-full">
                <summary className="font-bold text-base mb-3 mt-[44px] list-none hover:text-orange-300 transition-colors flex justify-between items-center pr-4 [&::-webkit-details-marker]:hidden">
                  Transportation
                  <svg className="w-4 h-4 transition-transform group-open:rotate-180" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
                </summary>
                <ul className="pl-0 space-y-2 opacity-80 text-sm overflow-hidden transition-all">
                  <li className="transition-transform hover:translate-x-2"><Link href={`/${locale}/transportation/train`} className="hover:underline block w-full">Train</Link></li>
                  <li className="transition-transform hover:translate-x-2"><Link href={`/${locale}/transportation/bus`} className="hover:underline block w-full">Bus</Link></li>
                  <li className="transition-transform hover:translate-x-2"><Link href={`/${locale}/transportation/car`} className="hover:underline block w-full">Rental Car</Link></li>
                </ul>
              </details>"""
content = re.sub(r'<div className="flex flex-col">\s*<h3 className="font-bold text-base mb-3 mt-\[44px\]">Transportation</h3>\s*<ul className="pl-0 space-y-2 opacity-80 text-sm">\s*<li>.*?Train.*?</li>\s*<li>.*?Bus.*?</li>\s*<li>.*?Rental Car.*?</li>\s*</ul>\s*</div>', desktop_trans, content, flags=re.DOTALL)


desktop_learn = """              <details open className="flex flex-col group cursor-pointer w-full">
                <summary className="font-bold text-base mb-3 mt-[44px] list-none hover:text-orange-300 transition-colors flex justify-between items-center pr-4 [&::-webkit-details-marker]:hidden">
                  Learning Materials
                  <svg className="w-4 h-4 transition-transform group-open:rotate-180" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
                </summary>
                <ul className="pl-0 space-y-2 opacity-80 text-sm overflow-hidden transition-all">
                  <li className="transition-transform hover:translate-x-2"><Link href={`/${locale}/learning-materials#alerts`} className="hover:underline block w-full">About Alerts</Link></li>
                  <li className="transition-transform hover:translate-x-2"><Link href={`/${locale}/learning-materials#power-outages`} className="hover:underline block w-full">Power outages</Link></li>
                  <li className="transition-transform hover:translate-x-2"><Link href={`/${locale}/learning-materials#links`} className="hover:underline block w-full">Links</Link></li>
                </ul>
              </details>"""
content = re.sub(r'<div className="flex flex-col">\s*<h3 className="font-bold text-base mb-3 mt-\[44px\]">Learning Materials</h3>\s*<ul className="pl-0 space-y-2 opacity-80 text-sm">\s*<li>.*?About Alerts.*?</li>\s*<li>.*?Power outages.*?</li>\s*<li>.*?Links.*?</li>\s*</ul>\s*</div>', desktop_learn, content, flags=re.DOTALL)

# Add missing top link animation
content = content.replace(
    '<Link href={`/${locale}`} className="font-bold text-lg">Top</Link>',
    '<Link href={`/${locale}`} className="font-bold text-lg hover:text-orange-300 transition-colors">Top</Link>'
)
content = content.replace(
    '<Link href={`/${locale}`} className="font-bold text-base hover:underline hover:opacity-100 transition-opacity">Top</Link>',
    '<Link href={`/${locale}`} className="font-bold text-base hover:text-orange-300 hover:underline hover:opacity-100 transition-all">Top</Link>'
)

with open('src/components/Footer.jsx', 'w') as out_f:
    out_f.write(content)
