import re

with open('src/app/[locale]/page.jsx', 'r') as f:
    content = f.read()

content = content.replace("t('todayWeatherTitle')", "t('weatherTitle')")
content = content.replace("t('maxTemp')", "t('weatherMax')")
content = content.replace("t('minTemp')", "t('weatherMin')")

# Add the banner title text for Desktop
banner_text_html = """
        <div className="absolute inset-0 w-full h-full">
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
        </div>
        
        {/* Desktop Banner Text Overlay */}
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
        </div>
"""

content = content.replace("""        <div className="absolute inset-0 w-full h-full">
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
        </div>""", banner_text_html)


# Also adjust the overlapping grid to be lower so it doesn't cover the text as much
content = content.replace('md:-mt-32 px-4', 'md:-mt-20 px-4')

with open('src/app/[locale]/page.jsx', 'w') as out_f:
    out_f.write(content)

