import re

with open('src/app/[locale]/page.jsx', 'r') as f:
    content = f.read()

# I will replace the return statement block.
start_idx = content.find('  return (')
if start_idx != -1:
    new_return = """  return (
    <div className="flex flex-col items-center pb-10 bg-[#f4f7f6]">
      {/* Hero Banner Section */}
      <section className="w-full h-[85vh] md:h-[70vh] min-h-[500px] relative flex flex-col items-center justify-start overflow-hidden pt-28 pb-32">
        {/* Banner Illustration Background */}
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
      </section>

      {/* Main Content Container */}
      <div className="w-full max-w-md md:max-w-5xl lg:max-w-6xl mx-auto relative z-20 -mt-24 md:-mt-32 px-4 md:px-0">
        
        {/* Weather & Earthquake Grid */}
        <div className="flex flex-col md:flex-row gap-4 md:gap-6 mb-8 md:mb-16 md:w-3/4 lg:w-2/3">
          
          {/* Weather Card */}
          <section className="w-full md:w-1/2 bg-white rounded-3xl p-6 shadow-xl flex-1">
            <div className="flex items-center gap-2 mb-2 text-gray-600">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/>
              </svg>
              <span className="text-sm font-medium">{t('location')}</span>
            </div>
            <h2 className="text-2xl font-bold text-green-500 mb-4">
              {t('todayWeatherTitle')}
            </h2>
            
            <div className={`bg-gradient-to-r ${bgGradient} rounded-2xl p-6 text-white flex flex-col relative overflow-hidden`}>
              <div className="relative z-10">
                <div className="text-6xl font-black mb-1">{currentTemp}°C</div>
                <div className="text-sm font-bold tracking-wide mt-2 opacity-90">
                  {t('maxTemp')} {maxTemp}°C, {t('minTemp')} {minTemp}°C
                </div>
              </div>
              <div className="absolute right-2 top-2 opacity-30">
                <svg width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  {code <= 3 ? (
                    <><circle cx="12" cy="12" r="5"/><path d="M12 1v2m0 18v2M4.22 4.22l1.42 1.42m12.72 12.72 1.42 1.42M1 12h2m18 0h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></>
                  ) : code <= 67 ? (
                    <><path d="M20 16.58A5 5 0 0 0 18 7h-1.26A8 8 0 1 0 4 15.25"/><path d="M16 13v8"/><path d="M8 13v8"/><path d="M12 15v8"/></>
                  ) : (
                    <><path d="M20 16.58A5 5 0 0 0 18 7h-1.26A8 8 0 1 0 4 15.25"/><path d="M8 22l4-10h4l-4 10"/></>
                  )}
                </svg>
              </div>
            </div>
          </section>

          {/* Earthquake Card */}
          <section className="w-full md:w-1/2 bg-white rounded-3xl p-6 shadow-xl flex-1">
            <div className="flex items-center gap-2 mb-2 text-gray-600">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/>
              </svg>
              <span className="text-sm font-medium">{t('location')}</span>
            </div>
            <h2 className="text-2xl font-bold text-green-500 mb-4">
              {t('recentEarthquakeTitle')}
            </h2>
            
            {earthquake ? (
              <div className="bg-gradient-to-r from-red-500 to-orange-400 rounded-2xl p-6 text-white flex flex-col relative overflow-hidden h-full">
                <div className="relative z-10">
                  <div className="text-5xl font-black mb-1">M {earthquake.properties.mag.toFixed(1)}</div>
                  <div className="text-sm font-bold tracking-wide mt-2 opacity-90 truncate" title={earthquake.properties.place}>
                    {earthquake.properties.place}
                  </div>
                  <div className="text-xs font-bold tracking-wide mt-1 opacity-75">
                    {new Date(earthquake.properties.time).toLocaleString(locale === 'th' ? 'th-TH' : 'en-US', {
                      timeZone: 'Asia/Tokyo',
                      month: 'short',
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit'
                    })}
                  </div>
                </div>
                <div className="absolute right-[-10px] bottom-[-20px] opacity-20">
                  <svg width="120" height="120" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M2 12h4l2-9 5 18 3-9h6"/>
                  </svg>
                </div>
              </div>
            ) : (
              <div className="bg-gray-200 rounded-2xl p-6 text-gray-500 text-center flex items-center justify-center h-full min-h-[120px]">
                {t('noEarthquakeData')}
              </div>
            )}
          </section>

        </div>

        {/* Scroll indicator */}
        <div className="flex flex-col items-center text-blue-600 animate-bounce mb-8">
          <span className="text-sm font-medium mb-1">{t('scroll')}</span>
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="6 9 12 15 18 9"></polyline>
          </svg>
        </div>

        {/* About Section */}
        <section className="w-full mb-12 text-gray-800 bg-white/60 md:bg-transparent rounded-3xl md:rounded-none p-6 md:p-0 shadow-sm md:shadow-none max-w-4xl">
          <div className="flex items-center gap-2 mb-4">
            <div className="w-3 h-3 rounded-full bg-green-500"></div>
            <h2 className="text-xl font-bold text-green-500">{t('aboutTitle')}</h2>
          </div>
          <p className="text-lg md:text-xl leading-relaxed">
            {t('aboutText')}
          </p>
        </section>

        {/* What Do You Need Section */}
        <section className="w-full bg-green-500 rounded-3xl p-6 md:p-10 pb-8 md:pb-12 mb-12 md:mb-20 shadow-lg">
          <h2 className="font-torsilp text-4xl md:text-6xl font-black text-white leading-tight mb-2 uppercase tracking-wider" dangerouslySetInnerHTML={{ __html: t.raw('whatDoYouNeed') }} />
          <div className="w-16 md:w-24 h-[2px] md:h-[3px] bg-white mb-4 md:mb-6"></div>
          <p className="text-white font-medium mb-6 md:mb-10">{t('pleaseSelect')}</p>

          <div className="space-y-6 md:space-y-0 md:grid md:grid-cols-3 md:gap-6">
            {/* Disaster */}
            <div className="bg-white rounded-2xl p-5 shadow-sm">
              <div className="flex justify-between items-center mb-4">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-orange-400"></div>
                  <h3 className="text-2xl font-bold text-black">{t('disaster')}</h3>
                </div>
                <div className="w-8 h-8 rounded-full bg-orange-400 flex justify-center items-center text-white">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="m9 18 6-6-6-6"/></svg>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <Link href={`/${locale}/disaster/blizzard`} className="block relative aspect-square rounded-xl overflow-hidden shadow-inner group">
                  <Image src="/illustrations/Blizzard.png" alt="Blizzard" fill className="object-cover group-hover:scale-105 transition-transform" />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent"></div>
                  <div className="absolute bottom-2 left-0 right-0 text-center text-white font-bold text-lg">{t('blizzard')}</div>
                </Link>
                <Link href={`/${locale}/disaster/earthquake`} className="block relative aspect-square rounded-xl overflow-hidden shadow-inner group">
                  <Image src="/illustrations/Earthquake .png" alt="Earthquake" fill className="object-cover group-hover:scale-105 transition-transform" />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent"></div>
                  <div className="absolute bottom-2 left-0 right-0 text-center text-white font-bold text-lg">{t('earthquake')}</div>
                </Link>
              </div>
            </div>

            {/* Transportation */}
            <div className="bg-white rounded-2xl p-5 shadow-sm">
              <div className="flex justify-between items-center mb-4">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-orange-400"></div>
                  <h3 className="text-2xl font-bold text-black">{t('transportation')}</h3>
                </div>
                <Link href={`/${locale}/transportation/train`} className="w-8 h-8 rounded-full bg-orange-400 flex justify-center items-center text-white">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="m9 18 6-6-6-6"/></svg>
                </Link>
              </div>
              <div className="relative aspect-[16/9] md:aspect-square w-full rounded-xl overflow-hidden shadow-inner bg-blue-50">
                <Image src="/illustrations/Transportation Homepage.png" alt="Transportation" fill className="object-cover md:object-cover" />
              </div>
            </div>

            {/* Learning Materials */}
            <div className="bg-white rounded-2xl p-5 shadow-sm">
              <div className="flex justify-between items-center mb-4">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-orange-400"></div>
                  <h3 className="text-2xl font-bold text-black leading-tight" dangerouslySetInnerHTML={{ __html: t.raw('learningMaterialsTitle') }} />
                </div>
                <Link href={`/${locale}/learning-materials`} className="w-8 h-8 rounded-full bg-orange-400 flex justify-center items-center text-white">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="m9 18 6-6-6-6"/></svg>
                </Link>
              </div>
              <div className="relative aspect-[16/9] md:aspect-square w-full rounded-xl overflow-hidden shadow-inner bg-green-50">
                <Image src="/illustrations/Learning mat.png" alt="Learning Materials" fill className="object-cover md:object-cover" />
              </div>
            </div>
          </div>
        </section>

        {/* Hokkaido Information Section */}
        <section className="w-full mb-8 relative md:flex md:items-center">
          <div className="md:w-1/2 relative z-10">
            <h2 className="font-torsilp text-4xl md:text-6xl font-black text-green-500 leading-none mb-4 uppercase tracking-wider" dangerouslySetInnerHTML={{ __html: t.raw('infoTitle') }} />
            <p className="text-gray-700 leading-relaxed text-lg md:text-xl" dangerouslySetInnerHTML={{ __html: t.raw('infoText') }} />
          </div>
          
          {/* Decorative Hokkaido Map Silhouette */}
          <div className="hidden md:block md:w-1/2 relative min-h-[400px]">
            <svg viewBox="0 0 500 500" className="w-full h-full text-white drop-shadow-md absolute inset-0 opacity-80" fill="currentColor">
              <path d="M 284.45312 95.839844 L 285.45312 119.83984 L 297.45312 129.83984 L 294.45312 144.83984 L 320.45312 178.83984 L 341.45312 184.83984 L 358.45312 165.83984 L 387.45312 161.83984 L 401.45312 188.83984 L 401.45312 211.83984 L 387.45312 218.83984 L 372.45312 245.83984 L 392.45312 258.83984 L 382.45312 291.83984 L 410.45312 300.83984 L 468.45312 300.83984 L 480.45312 316.83984 L 462.45312 344.83984 L 439.45312 360.83984 L 409.45312 367.83984 L 400.45312 391.83984 L 397.45312 405.83984 L 379.45312 396.83984 L 370.45312 370.83984 L 333.45312 357.83984 L 305.45312 343.83984 L 298.45312 366.83984 L 273.45312 384.83984 L 261.45312 365.83984 L 243.45312 376.83984 L 235.45312 429.83984 L 210.45312 447.83984 L 217.45312 411.83984 L 202.45312 402.83984 L 221.45312 375.83984 L 180.45312 373.83984 L 166.45312 360.83984 L 129.45312 359.83984 L 118.45312 368.83984 L 124.45312 380.83984 L 105.45312 376.83984 L 111.45312 350.83984 L 97.45312 344.83984 L 94.45312 331.83984 L 128.45312 320.83984 L 132.45312 301.83984 L 122.45312 284.83984 L 90.453125 301.83984 L 83.453125 289.83984 L 56.453125 273.83984 L 23.453125 277.83984 L 32.453125 258.83984 L 51.453125 240.83984 L 46.453125 210.83984 L 79.453125 220.83984 L 106.45312 186.83984 L 134.45312 187.83984 L 160.45312 201.83984 L 175.45312 201.83984 L 181.45312 216.83984 L 224.45312 216.83984 L 238.45312 173.83984 L 244.45312 129.83984 L 261.45312 108.83984 L 284.45312 95.839844 Z" />
            </svg>
          </div>
        </section>

      </div>
    </div>
  );
}
"""

    new_content = content[:start_idx] + new_return
    with open('src/app/[locale]/page.jsx', 'w') as out_f:
        out_f.write(new_content)
else:
    print("Could not find start index")
