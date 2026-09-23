import Link from "next/link";
import { getTranslations } from 'next-intl/server';

export default async function LearningMaterialsPage({ params }) {
  const { locale } = await params;
  const t = await getTranslations('LearningMaterials');
  const tBlizzard = await getTranslations('Blizzard'); // Reusing linksTitle translation if needed
  
  return (
    <div className="flex flex-col items-center pb-10 bg-[#f4f7f6] pt-24">
      <div className="w-[90%] max-w-md md:max-w-5xl lg:max-w-6xl">
        
        {/* Header */}
        <h1 className="font-mittraphap text-5xl md:text-8xl font-black text-black tracking-wider mb-2 md:mb-6 leading-none uppercase" dangerouslySetInnerHTML={{ __html: t.raw('title') }} />
        <div className="border-b-2 border-dashed border-gray-400 mb-8 md:mb-12"></div>

        {/* Desktop Wrapper for White Card */}
        <div className="md:bg-white md:rounded-[32px] md:shadow-md md:p-10 mb-12">

          {/* Section 1: Alerts */}
          <div id="alerts" className="bg-white rounded-3xl shadow-md p-6 mb-6 md:bg-transparent md:shadow-none md:p-0 md:rounded-none md:mb-12 scroll-mt-32">
            <h2 className="text-2xl md:text-4xl font-bold text-black mb-4 leading-tight">
              {t('alertsTitle')}
            </h2>
            <p className="text-gray-700 leading-relaxed mb-6 md:mb-10">
              {t('alertsDesc')}
            </p>

            <div className="flex items-center gap-2 mb-2">
              <div className="w-3 h-3 rounded-full bg-green-700 shrink-0"></div>
              <h3 className="text-xl md:text-2xl font-bold text-black">{t('mainLevels')}</h3>
            </div>
            <p className="text-gray-700 mb-4 md:mb-6">{t('mainLevelsDesc')}</p>

            <div className="space-y-4 md:space-y-0 md:grid md:grid-cols-3 md:gap-6">
              {/* Level 1 */}
              <div className="border-2 border-black rounded-2xl p-4 md:p-6 bg-white">
                <div className="flex justify-between items-start mb-3">
                  <h4 className="font-bold text-lg text-black leading-tight" dangerouslySetInnerHTML={{ __html: t.raw('level1Title') }} />
                  <div className="bg-green-700 text-white font-bold text-sm py-1 px-3 rounded-lg shrink-0">
                    {t('level1Badge')}
                  </div>
                </div>
                <div className="border-b-2 border-dashed border-gray-300 mb-3"></div>
                <p className="text-gray-700 text-sm" dangerouslySetInnerHTML={{ __html: t.raw('level1Desc') }} />
              </div>

              {/* Level 2 */}
              <div className="border-2 border-black rounded-2xl p-4 md:p-6 bg-white">
                <div className="flex justify-between items-start mb-3">
                  <h4 className="font-bold text-lg text-black leading-tight" dangerouslySetInnerHTML={{ __html: t.raw('level2Title') }} />
                  <div className="bg-orange-400 text-white font-bold text-sm py-1 px-3 rounded-lg shrink-0">
                    {t('level2Badge')}
                  </div>
                </div>
                <div className="border-b-2 border-dashed border-gray-300 mb-3"></div>
                <p className="text-gray-700 text-sm" dangerouslySetInnerHTML={{ __html: t.raw('level2Desc') }} />
              </div>

              {/* Level 3 */}
              <div className="border-2 border-black rounded-2xl p-4 md:p-6 bg-white">
                <div className="flex justify-between items-start mb-3">
                  <h4 className="font-bold text-lg text-black leading-tight" dangerouslySetInnerHTML={{ __html: t.raw('level3Title') }} />
                  <div className="bg-white border-2 border-black text-black font-bold text-sm py-1 px-3 rounded-lg shrink-0">
                    {t('level3Badge')}
                  </div>
                </div>
                <div className="border-b-2 border-dashed border-gray-300 mb-3"></div>
                <p className="text-gray-700 text-sm" dangerouslySetInnerHTML={{ __html: t.raw('level3Desc') }} />
              </div>
            </div>
          </div>

          {/* Section 2: Power Outages */}
          <div id="power-outages" className="bg-white rounded-3xl shadow-md p-6 mb-10 md:bg-transparent md:shadow-none md:p-0 md:rounded-none md:mb-0 scroll-mt-32">
            <div className="flex items-center gap-2 mb-4">
              <svg className="text-green-700 w-6 h-6 shrink-0 md:w-8 md:h-8" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M11 20.03c-5.5-.32-10-4.9-10-10.45 0-5.78 4.7-10.46 10.48-10.46 5.78 0 10.46 4.68 10.46 10.46 0 5.55-4.5 10.13-10 10.45"/><path d="m11 2-2 9h4l-2 9"/></svg>
              <h2 className="text-2xl md:text-3xl font-bold text-black">{t('powerTitle')}</h2>
            </div>
            
            <p className="text-gray-700 leading-relaxed mb-6 md:mb-10">
              {t('powerIntro')}
            </p>

            <div className="md:grid md:grid-cols-2 md:gap-12">
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-3 h-3 rounded-full bg-green-700 shrink-0"></div>
                  <h3 className="text-xl md:text-2xl font-bold text-black">{t('prepTitle')}</h3>
                </div>
                <div className="text-gray-700 mb-6 space-y-2 pl-5 md:mb-0">
                  <p>{t('prep1')}</p>
                  <p>{t('prep2')}</p>
                  <p>{t('prep3')}</p>
                </div>
              </div>

              <div>
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-3 h-3 rounded-full bg-green-700 shrink-0"></div>
                  <h3 className="text-xl md:text-2xl font-bold text-black">{t('powerOutTitle')}</h3>
                </div>
                <div className="text-gray-700 space-y-2 pl-5">
                  <p>{t('out1')}</p>
                  <p>{t('out2')}</p>
                  <p>{t('out3')}</p>
                </div>
              </div>
            </div>
          </div>
          
        </div>

        {/* Section 3: Help desk & Links */}
        {/* On mobile it's a white card, on desktop it's a transparent section matching Disaster Links */}
        <div id="links" className="bg-white rounded-3xl shadow-md p-6 mb-10 md:bg-transparent md:shadow-none md:p-0 md:rounded-none scroll-mt-32">
          
          <div className="md:hidden">
            <div className="flex items-center gap-2 mb-4">
              <svg className="text-green-700 w-6 h-6 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/><path d="M2 12h20"/>
              </svg>
              <h2 className="text-2xl font-bold text-black">{t('helpDeskTitle')}</h2>
            </div>
            
            <p className="text-gray-700 leading-relaxed mb-6">
              {t('helpDeskIntro')}
            </p>
          </div>

          <div className="hidden md:block">
            <h2 className="font-mittraphap text-7xl font-black text-black tracking-wider mb-2 mt-12 uppercase">{t('helpDeskTitle')}</h2>
            <div className="border-b-2 border-dashed border-gray-400 mb-10"></div>
          </div>

          <div className="space-y-4 md:space-y-0 md:grid md:grid-cols-2 md:gap-8">
            <Link href="https://www.japan.travel/en/plan/hotline/" target="_blank" rel="noopener noreferrer" className="flex flex-col md:flex-row md:items-center p-4 md:p-6 border-2 border-black md:border-none md:bg-white md:shadow-sm md:rounded-2xl hover:bg-gray-50 md:hover:shadow-md transition-all group md:justify-between">
              <div className="md:flex-1 md:pr-4">
                <div className="md:flex md:items-center md:gap-2 mb-1 md:mb-2">
                  <div className="hidden md:block w-3 h-3 rounded-full bg-green-700 shrink-0"></div>
                  <span className="font-bold text-black text-lg md:text-xl">{t('link1Title')}</span>
                </div>
                <div className="hidden md:block border-t border-dashed border-gray-300 pt-2 mt-2">
                  <p className="text-gray-600 text-sm">Disaster and safety information for travelers.</p>
                </div>
                <span className="text-sm text-blue-600 break-all underline decoration-blue-300 underline-offset-2 md:hidden">https://www.japan.travel/en/plan/hotline/</span>
              </div>
              <div className="hidden md:flex w-10 h-10 bg-orange-400 rounded-full justify-center items-center text-white shrink-0 group-hover:scale-110 transition-transform shadow-sm">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="m9 18 6-6-6-6"/></svg>
              </div>
            </Link>
            
            <Link href="https://www.japan.travel/en/news/JapanSafeTravel/" target="_blank" rel="noopener noreferrer" className="flex flex-col md:flex-row md:items-center p-4 md:p-6 border-2 border-black md:border-none md:bg-white md:shadow-sm md:rounded-2xl hover:bg-gray-50 md:hover:shadow-md transition-all group md:justify-between">
              <div className="md:flex-1 md:pr-4">
                <div className="md:flex md:items-center md:gap-2 mb-1 md:mb-2">
                  <div className="hidden md:block w-3 h-3 rounded-full bg-green-700 shrink-0"></div>
                  <span className="font-bold text-black text-lg md:text-xl">{t('link2Title')}</span>
                </div>
                <div className="hidden md:block border-t border-dashed border-gray-300 pt-2 mt-2">
                  <p className="text-gray-600 text-sm">Travel updates and safe travel tips.</p>
                </div>
                <span className="text-sm text-blue-600 break-all underline decoration-blue-300 underline-offset-2 md:hidden">https://www.japan.travel/en/news/JapanSafeTravel/</span>
              </div>
              <div className="hidden md:flex w-10 h-10 bg-orange-400 rounded-full justify-center items-center text-white shrink-0 group-hover:scale-110 transition-transform shadow-sm">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="m9 18 6-6-6-6"/></svg>
              </div>
            </Link>

            <Link href="https://crisis.yahoo.co.jp/map/" target="_blank" rel="noopener noreferrer" className="flex flex-col md:flex-row md:items-center p-4 md:p-6 border-2 border-black md:border-none md:bg-white md:shadow-sm md:rounded-2xl hover:bg-gray-50 md:hover:shadow-md transition-all group md:justify-between">
              <div className="md:flex-1 md:pr-4">
                <div className="md:flex md:items-center md:gap-2 mb-1 md:mb-2">
                  <div className="hidden md:block w-3 h-3 rounded-full bg-green-700 shrink-0"></div>
                  <span className="font-bold text-black text-lg md:text-xl">{t('link3Title')}</span>
                </div>
                <div className="hidden md:block border-t border-dashed border-gray-300 pt-2 mt-2">
                  <p className="text-gray-600 text-sm">Crisis mapping and information.</p>
                </div>
                <span className="text-sm text-blue-600 break-all underline decoration-blue-300 underline-offset-2 md:hidden">https://crisis.yahoo.co.jp/map/</span>
              </div>
              <div className="hidden md:flex w-10 h-10 bg-orange-400 rounded-full justify-center items-center text-white shrink-0 group-hover:scale-110 transition-transform shadow-sm">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="m9 18 6-6-6-6"/></svg>
              </div>
            </Link>
            
            <Link href="https://wwwtb.mlit.go.jp/hokkaido/unkoujouhou/index.html" target="_blank" rel="noopener noreferrer" className="flex flex-col md:flex-row md:items-center p-4 md:p-6 border-2 border-black md:border-none md:bg-white md:shadow-sm md:rounded-2xl hover:bg-gray-50 md:hover:shadow-md transition-all group md:justify-between">
              <div className="md:flex-1 md:pr-4">
                <div className="md:flex md:items-center md:gap-2 mb-1 md:mb-2">
                  <div className="hidden md:block w-3 h-3 rounded-full bg-green-700 shrink-0"></div>
                  <span className="font-bold text-black text-lg md:text-xl">{t('link4Title')}</span>
                </div>
                <div className="hidden md:block border-t border-dashed border-gray-300 pt-2 mt-2">
                  <p className="text-gray-600 text-sm">Hokkaido transportation status.</p>
                </div>
                <span className="text-sm text-blue-600 break-all underline decoration-blue-300 underline-offset-2 md:hidden">https://wwwtb.mlit.go.jp/hokkaido/unkoujouhou/index.html</span>
              </div>
              <div className="hidden md:flex w-10 h-10 bg-orange-400 rounded-full justify-center items-center text-white shrink-0 group-hover:scale-110 transition-transform shadow-sm">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="m9 18 6-6-6-6"/></svg>
              </div>
            </Link>
            
            <Link href="https://www.jrhokkaido.co.jp/global/index.html" target="_blank" rel="noopener noreferrer" className="flex flex-col md:flex-row md:items-center p-4 md:p-6 border-2 border-black md:border-none md:bg-white md:shadow-sm md:rounded-2xl hover:bg-gray-50 md:hover:shadow-md transition-all group md:justify-between">
              <div className="md:flex-1 md:pr-4">
                <div className="md:flex md:items-center md:gap-2 mb-1 md:mb-2">
                  <div className="hidden md:block w-3 h-3 rounded-full bg-green-700 shrink-0"></div>
                  <span className="font-bold text-black text-lg md:text-xl">{t('link5Title')}</span>
                </div>
                <div className="hidden md:block border-t border-dashed border-gray-300 pt-2 mt-2">
                  <p className="text-gray-600 text-sm">JR Hokkaido Railway Company.</p>
                </div>
                <span className="text-sm text-blue-600 break-all underline decoration-blue-300 underline-offset-2 md:hidden">https://www.jrhokkaido.co.jp/global/index.html</span>
              </div>
              <div className="hidden md:flex w-10 h-10 bg-orange-400 rounded-full justify-center items-center text-white shrink-0 group-hover:scale-110 transition-transform shadow-sm">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="m9 18 6-6-6-6"/></svg>
              </div>
            </Link>
            
            <Link href="https://www.jrhokkaidobus.com/en/" target="_blank" rel="noopener noreferrer" className="flex flex-col md:flex-row md:items-center p-4 md:p-6 border-2 border-black md:border-none md:bg-white md:shadow-sm md:rounded-2xl hover:bg-gray-50 md:hover:shadow-md transition-all group md:justify-between">
              <div className="md:flex-1 md:pr-4">
                <div className="md:flex md:items-center md:gap-2 mb-1 md:mb-2">
                  <div className="hidden md:block w-3 h-3 rounded-full bg-green-700 shrink-0"></div>
                  <span className="font-bold text-black text-lg md:text-xl">{t('link6Title')}</span>
                </div>
                <div className="hidden md:block border-t border-dashed border-gray-300 pt-2 mt-2">
                  <p className="text-gray-600 text-sm">JR Hokkaido Bus Company.</p>
                </div>
                <span className="text-sm text-blue-600 break-all underline decoration-blue-300 underline-offset-2 md:hidden">https://www.jrhokkaidobus.com/en/</span>
              </div>
              <div className="hidden md:flex w-10 h-10 bg-orange-400 rounded-full justify-center items-center text-white shrink-0 group-hover:scale-110 transition-transform shadow-sm">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="m9 18 6-6-6-6"/></svg>
              </div>
            </Link>
          </div>
        </div>

      </div>
    </div>
  );
}

