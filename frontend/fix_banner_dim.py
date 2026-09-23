import re

with open('src/app/[locale]/page.jsx', 'r') as f:
    content = f.read()

old_block = """        <div className="absolute inset-0 w-full h-full">
          <Image 
            src="/illustrations/Banner.png" 
            alt="SafetyHokaido Mascot Waving" 
            fill 
            className="object-cover object-top md:hidden"
            priority
          />
          <Image 
            src="/illustrations/Banner_landscape.jpeg" 
            alt="SafetyHokaido Mascot Waving Desktop" 
            fill 
            className="object-cover object-center hidden md:block"
            priority
          />
        </div>"""

new_block = """        <div className="absolute inset-0 w-full h-full">
          <Image 
            src="/illustrations/Banner.png" 
            alt="SafetyHokaido Mascot Waving" 
            fill 
            className="object-cover object-top md:hidden brightness-[0.80]"
            priority
          />
          <Image 
            src="/illustrations/Banner_landscape.jpeg" 
            alt="SafetyHokaido Mascot Waving Desktop" 
            fill 
            className="object-cover object-center hidden md:block brightness-[0.80]"
            priority
          />
        </div>"""

content = content.replace(old_block, new_block)

with open('src/app/[locale]/page.jsx', 'w') as out_f:
    out_f.write(content)
