import re

with open('src/app/[locale]/page.jsx', 'r') as f:
    content = f.read()

old_svg_block = """          {/* Decorative Hokkaido Map Silhouette */}
          <div className="hidden md:block md:w-1/2 relative min-h-[400px]">
            <svg viewBox="0 0 500 500" className="w-full h-full text-white drop-shadow-md absolute inset-0 opacity-80" fill="currentColor">
              <path d="M 284.45312 95.839844 L 285.45312 119.83984 L 297.45312 129.83984 L 294.45312 144.83984 L 320.45312 178.83984 L 341.45312 184.83984 L 358.45312 165.83984 L 387.45312 161.83984 L 401.45312 188.83984 L 401.45312 211.83984 L 387.45312 218.83984 L 372.45312 245.83984 L 392.45312 258.83984 L 382.45312 291.83984 L 410.45312 300.83984 L 468.45312 300.83984 L 480.45312 316.83984 L 462.45312 344.83984 L 439.45312 360.83984 L 409.45312 367.83984 L 400.45312 391.83984 L 397.45312 405.83984 L 379.45312 396.83984 L 370.45312 370.83984 L 333.45312 357.83984 L 305.45312 343.83984 L 298.45312 366.83984 L 273.45312 384.83984 L 261.45312 365.83984 L 243.45312 376.83984 L 235.45312 429.83984 L 210.45312 447.83984 L 217.45312 411.83984 L 202.45312 402.83984 L 221.45312 375.83984 L 180.45312 373.83984 L 166.45312 360.83984 L 129.45312 359.83984 L 118.45312 368.83984 L 124.45312 380.83984 L 105.45312 376.83984 L 111.45312 350.83984 L 97.45312 344.83984 L 94.45312 331.83984 L 128.45312 320.83984 L 132.45312 301.83984 L 122.45312 284.83984 L 90.453125 301.83984 L 83.453125 289.83984 L 56.453125 273.83984 L 23.453125 277.83984 L 32.453125 258.83984 L 51.453125 240.83984 L 46.453125 210.83984 L 79.453125 220.83984 L 106.45312 186.83984 L 134.45312 187.83984 L 160.45312 201.83984 L 175.45312 201.83984 L 181.45312 216.83984 L 224.45312 216.83984 L 238.45312 173.83984 L 244.45312 129.83984 L 261.45312 108.83984 L 284.45312 95.839844 Z" />
            </svg>
          </div>"""

new_image_block = """          {/* Decorative Hokkaido Map Silhouette */}
          <div className="hidden md:block md:w-1/2 relative min-h-[350px]">
            <Image 
              src="/illustrations/hokkaido.png" 
              alt="Hokkaido Map Silhouette" 
              fill 
              className="object-contain opacity-90 drop-shadow-md p-4"
            />
          </div>"""

content = content.replace(old_svg_block, new_image_block)

with open('src/app/[locale]/page.jsx', 'w') as out_f:
    out_f.write(content)
