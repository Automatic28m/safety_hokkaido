import Image from "next/image";
import Link from "next/link";
import { getTranslations } from 'next-intl/server';

async function getWeatherData() {
  try {
    const res = await fetch("https://api.open-meteo.com/v1/forecast?latitude=43.0621&longitude=141.3544&current=temperature_2m,weather_code&daily=temperature_2m_max,temperature_2m_min&timezone=Asia%2FTokyo", {
      next: { revalidate: 1800 } // Revalidate every 30 mins
    });
    if (!res.ok) throw new Error('Failed to fetch weather');
    return res.json();
  } catch (error) {
    console.error("Weather fetch error:", error);
    return null;
  }
}

export default async function Home({ params }) {
  const { locale } = await params;
  const t = await getTranslations('Home');
  const weatherData = await getWeatherData();
  
  // Fallbacks in case API fails
  const currentTemp = weatherData?.current?.temperature_2m ? Math.round(weatherData.current.temperature_2m) : 25;
  const maxTemp = weatherData?.daily?.temperature_2m_max?.[0] ? Math.round(weatherData.daily.temperature_2m_max[0]) : 27;
  const minTemp = weatherData?.daily?.temperature_2m_min?.[0] ? Math.round(weatherData.daily.temperature_2m_min[0]) : 15;
  
  const code = weatherData?.current?.weather_code || 0;
  let bgGradient = "from-yellow-400 to-orange-500"; // Sunny
  if (code >= 51 && code <= 67) bgGradient = "from-blue-400 to-indigo-600"; // Rain
  else if (code >= 71 && code <= 86) bgGradient = "from-slate-300 to-slate-500"; // Snow
  else if (code >= 1 && code <= 3) bgGradient = "from-sky-300 to-blue-400"; // Cloudy
  else if (code >= 95) bgGradient = "from-gray-600 to-gray-900"; // Thunderstorm

  // Fetch earthquake data
  let earthquake = null;
  try {
    const res = await fetch('https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&limit=1&orderby=time&minlatitude=30&maxlatitude=46&minlongitude=128&maxlongitude=146', { next: { revalidate: 60 } });
    if (res.ok) {
      const data = await res.json();
      if (data.features && data.features.length > 0) {
        earthquake = data.features[0];
      }
    }
  } catch (err) {
    console.error("Failed to fetch earthquake data:", err);
  }

  return (
    <div className="flex flex-col items-center pb-10 bg-[#f4f7f6]">
      {/* Hero Banner Section */}
      <section className="w-full h-[85vh] md:h-[70vh] min-h-[500px] relative flex flex-col items-center justify-start overflow-hidden pt-36 pb-32">
        {/* Banner Illustration Background */}

        <div className="absolute inset-0 w-full h-full">
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
        </div>
        
        {/* Banner Text Overlay (Mobile + Desktop) */}
        <div className="flex absolute left-0 w-full h-full z-10 pointer-events-none">
          <div className="w-full max-w-md md:max-w-5xl lg:max-w-6xl mx-auto px-6 md:px-0 pt-24 md:pt-28">
            <h1 className="font-mittraphap text-white font-black leading-none drop-shadow-[0_4px_4px_rgba(0,0,0,0.3)] flex flex-col uppercase tracking-wider text-[3.5rem] md:text-[clamp(4rem,8vw,7rem)]">
              <span>Safety</span>
              <span>Hokkaido</span>
            </h1>
            <p className="text-white text-lg md:text-xl lg:text-2xl mt-2 md:mt-4 font-bold drop-shadow-[0_2px_2px_rgba(0,0,0,0.4)] max-w-[200px] md:max-w-md leading-tight">
              {t('subtitle')}
            </p>
          </div>
        </div>

      </section>

      {/* Main Content Container */}
      <div className="w-full max-w-md md:max-w-5xl lg:max-w-6xl mx-auto relative z-20 -mt-24 md:-mt-20 px-4 md:px-0">
        
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
            <h2 className="text-2xl font-bold text-green-700 mb-4">
              {t('weatherTitle')}
            </h2>
            
            <div className={`bg-gradient-to-r ${bgGradient} rounded-2xl p-6 text-white flex flex-col relative overflow-hidden`}>
              <div className="relative z-10">
                <div className="text-6xl font-black mb-1">{currentTemp}°C</div>
                <div className="text-sm font-bold tracking-wide mt-2 opacity-90">
                  {t('weatherMax')} {maxTemp}°C, {t('weatherMin')} {minTemp}°C
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
            <h2 className="text-2xl font-bold text-green-700 mb-4">
              {t('recentEarthquakeTitle')}
            </h2>
            
            {earthquake ? (
              <div className="bg-gradient-to-r from-red-500 to-orange-400 rounded-2xl p-6 text-white flex flex-col relative overflow-hidden">
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
            <div className="w-3 h-3 rounded-full bg-green-700"></div>
            <h2 className="text-xl font-bold text-green-700">{t('aboutTitle')}</h2>
          </div>
          <p className="text-lg md:text-xl leading-relaxed">
            {t('aboutText')}
          </p>
        </section>

        {/* What Do You Need Section */}
        <section className="w-full bg-green-700 rounded-3xl p-6 md:p-10 pb-8 md:pb-12 mb-12 md:mb-20 shadow-lg">
          <h2 className="font-mittraphap text-4xl md:text-6xl font-black text-white leading-tight mb-2 uppercase tracking-wider" dangerouslySetInnerHTML={{ __html: t.raw('whatDoYouNeed') }} />
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
              <div className="grid grid-rows-2 gap-3">
                <Link href={`/${locale}/disaster/blizzard`} className="block relative aspect-video rounded-xl overflow-hidden shadow-inner group">
                  <Image src="/illustrations/Blizzard.png" alt="Blizzard" fill className="object-cover group-hover:scale-105 transition-transform" />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent"></div>
                  <div className="absolute bottom-2 left-0 right-0 text-center text-white font-bold text-lg">{t('blizzard')}</div>
                </Link>
                <Link href={`/${locale}/disaster/earthquake`} className="block relative aspect-video rounded-xl overflow-hidden shadow-inner group">
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
            <h2 className="font-mittraphap text-4xl md:text-6xl font-black text-green-700 leading-none mb-4 uppercase tracking-wider" dangerouslySetInnerHTML={{ __html: t.raw('infoTitle') }} />
            <p className="text-gray-700 leading-relaxed text-lg md:text-xl" dangerouslySetInnerHTML={{ __html: t.raw('infoText') }} />
          </div>
          
          {/* Decorative Hokkaido Map Silhouette */}
          <div className="hidden md:block md:w-1/2 relative min-h-[350px]">
            <Image 
              src="/illustrations/hokkaido.png" 
              alt="Hokkaido Map Silhouette" 
              fill 
              className="object-contain opacity-90 drop-shadow-md p-4"
            />
          </div>
        </section>

      </div>
    </div>
  );
}
