import re

with open('src/app/[locale]/page.jsx', 'r') as f:
    content = f.read()

# Replace the text overlay block
old_overlay = """        {/* Desktop Banner Text Overlay */}
        <div className="hidden md:flex absolute top-0 left-0 w-full h-full z-10">
          <div className="w-full max-w-md md:max-w-5xl lg:max-w-6xl mx-auto px-4 md:px-0 pt-28">
            <h1 className="font-torsilp text-white font-black leading-none drop-shadow-md flex flex-col uppercase tracking-wider" style={{ fontSize: 'clamp(4rem, 8vw, 7rem)' }}>
              <span>Safety</span>
              <span>Hokaido</span>
            </h1>
            <p className="text-white text-xl lg:text-2xl mt-4 font-medium drop-shadow-md max-w-md">
              Hokkaido Disaster Guide for Tourist
            </p>
          </div>
        </div>"""

new_overlay = """        {/* Banner Text Overlay (Mobile + Desktop) */}
        <div className="flex absolute top-0 left-0 w-full h-full z-10 pointer-events-none">
          <div className="w-full max-w-md md:max-w-5xl lg:max-w-6xl mx-auto px-6 md:px-0 pt-24 md:pt-28">
            <h1 className="font-torsilp text-white font-black leading-none drop-shadow-[0_4px_4px_rgba(0,0,0,0.3)] flex flex-col uppercase tracking-wider text-[3.5rem] md:text-[clamp(4rem,8vw,7rem)]">
              <span>Safety</span>
              <span>Hokaido</span>
            </h1>
            <p className="text-white text-lg md:text-xl lg:text-2xl mt-2 md:mt-4 font-bold drop-shadow-[0_2px_2px_rgba(0,0,0,0.4)] max-w-[200px] md:max-w-md leading-tight">
              Hokkaido Disaster Guide for Tourist
            </p>
          </div>
        </div>"""

content = content.replace(old_overlay, new_overlay)

with open('src/app/[locale]/page.jsx', 'w') as out_f:
    out_f.write(content)
