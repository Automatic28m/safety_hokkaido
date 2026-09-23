import re

with open('src/app/[locale]/disaster/earthquake/page.jsx', 'r') as f:
    content = f.read()

old_block = """          {/* Desktop Tsunami separator */}
          <div className="hidden md:block relative mt-8 mb-16">
            <div className="absolute left-16 top-[-40px] border-l-2 border-dashed border-gray-400 h-16"></div>
            <div className="absolute left-20 top-[-40px] bg-[#0047b3] text-white text-sm font-bold py-2 px-4 rounded-r-xl rounded-bl-xl shadow-md w-64">
              <span dangerouslySetInnerHTML={{ __html: t.raw('tsunamiBanner') }} />
              <div className="absolute w-3 h-3 bg-[#0047b3] rotate-45 -left-1.5 top-3"></div>
            </div>
          </div>

          <div className="pt-16 md:pt-0">
            <h2 className="font-torsilp text-4xl md:text-6xl font-black text-black mb-4">{t('tsunamiHeading')}</h2>"""


new_block = """          {/* Desktop Tsunami separator */}
          <div className="hidden md:block relative h-24 w-full">
            <div className="absolute left-4 top-[-20px] border-l-2 border-dashed border-gray-400 h-16 z-0"></div>
            <div className="absolute left-8 top-[-10px] bg-[#0047b3] text-white text-sm font-bold py-2 px-4 rounded-r-xl rounded-bl-xl shadow-md w-[280px] z-10">
              <span dangerouslySetInnerHTML={{ __html: t.raw('tsunamiBanner') }} />
              <div className="absolute w-3 h-3 bg-[#0047b3] rotate-45 -left-1.5 top-3"></div>
            </div>
          </div>

          <div className="pt-16 md:pt-0">
            <h2 className="font-torsilp text-4xl md:text-6xl font-black text-black mb-4">{t('tsunamiHeading')}</h2>"""

content = content.replace(old_block, new_block)

with open('src/app/[locale]/disaster/earthquake/page.jsx', 'w') as out_f:
    out_f.write(content)
