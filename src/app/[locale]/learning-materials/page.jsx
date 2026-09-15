import Link from "next/link";

import { getTranslations } from 'next-intl/server';

export default async function LearningMaterialsPage({ params }) {
  const { locale } = await params;
  const t = await getTranslations('LearningMaterials');
  return (
    <div className="flex flex-col items-center pb-10 bg-[#f4f7f6] pt-24">
      <div className="w-[90%] max-w-md">
        
        {/* Header */}
        <h1 className="font-torsilp text-5xl font-black text-black tracking-wider mb-2 leading-none uppercase" dangerouslySetInnerHTML={{ __html: t.raw('title') }} />
        <div className="border-b-2 border-dashed border-gray-400 mb-8"></div>

        {/* Section 1: Alerts */}
        <div id="alerts" className="bg-white rounded-3xl shadow-md p-6 mb-6 scroll-mt-32">
          <h2 className="text-2xl font-bold text-black mb-4 leading-tight">
            {t('alertsTitle')}
          </h2>
          <p className="text-gray-700 leading-relaxed mb-6">
            {t('alertsDesc')}
          </p>

          <div className="flex items-center gap-2 mb-2">
            <div className="w-3 h-3 rounded-full bg-green-500 shrink-0"></div>
            <h3 className="text-xl font-bold text-black">{t('mainLevels')}</h3>
          </div>
          <p className="text-gray-700 mb-4">{t('mainLevelsDesc')}</p>

          <div className="space-y-4">
            {/* Level 1 */}
            <div className="border-2 border-black rounded-2xl p-4">
              <div className="flex justify-between items-start mb-3">
                <h4 className="font-bold text-lg text-black leading-tight" dangerouslySetInnerHTML={{ __html: t.raw('level1Title') }} />
                <div className="bg-green-500 text-white font-bold text-sm py-1 px-3 rounded-lg shrink-0">
                  {t('level1Badge')}
                </div>
              </div>
              <div className="border-b-2 border-dashed border-gray-300 mb-3"></div>
              <p className="text-gray-700 text-sm" dangerouslySetInnerHTML={{ __html: t.raw('level1Desc') }} />
            </div>

            {/* Level 2 */}
            <div className="border-2 border-black rounded-2xl p-4">
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
            <div className="border-2 border-black rounded-2xl p-4">
              <div className="flex justify-between items-start mb-3">
                <h4 className="font-bold text-lg text-black leading-tight" dangerouslySetInnerHTML={{ __html: t.raw('level3Title') }} />
                <div className="bg-red-600 text-white font-bold text-sm py-1 px-3 rounded-lg shrink-0">
                  {t('level3Badge')}
                </div>
              </div>
              <div className="border-b-2 border-dashed border-gray-300 mb-3"></div>
              <p className="text-gray-700 text-sm" dangerouslySetInnerHTML={{ __html: t.raw('level3Desc') }} />
            </div>
          </div>
        </div>

        {/* Section 2: Power Outages */}
        <div id="power-outages" className="bg-white rounded-3xl shadow-md p-6 mb-10 scroll-mt-32">
          <div className="flex items-center gap-2 mb-4">
            <svg className="text-green-500 w-6 h-6 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M11 20.03c-5.5-.32-10-4.9-10-10.45 0-5.78 4.7-10.46 10.48-10.46 5.78 0 10.46 4.68 10.46 10.46 0 5.55-4.5 10.13-10 10.45"/><path d="m11 2-2 9h4l-2 9"/></svg>
            <h2 className="text-2xl font-bold text-black">{t('powerTitle')}</h2>
          </div>
          
          <p className="text-gray-700 leading-relaxed mb-6">
            {t('powerIntro')}
          </p>

          <div className="flex items-center gap-2 mb-2">
            <div className="w-3 h-3 rounded-full bg-green-500 shrink-0"></div>
            <h3 className="text-xl font-bold text-black">{t('prepTitle')}</h3>
          </div>
          <div className="text-gray-700 mb-6 space-y-2 pl-5">
            <p>{t('prep1')}</p>
            <p>{t('prep2')}</p>
            <p>{t('prep3')}</p>
          </div>

          <div className="flex items-center gap-2 mb-2">
            <div className="w-3 h-3 rounded-full bg-green-500 shrink-0"></div>
            <h3 className="text-xl font-bold text-black">{t('powerOutTitle')}</h3>
          </div>
          <div className="text-gray-700 space-y-2 pl-5">
            <p>{t('out1')}</p>
            <p>{t('out2')}</p>
            <p>{t('out3')}</p>
          </div>
        </div>
        {/* Section 3: Help desk & Links */}
        <div id="links" className="bg-white rounded-3xl shadow-md p-6 mb-10 scroll-mt-32">
          <div className="flex items-center gap-2 mb-4">
            <svg className="text-green-500 w-6 h-6 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/><path d="M2 12h20"/>
            </svg>
            <h2 className="text-2xl font-bold text-black">{t('helpDeskTitle')}</h2>
          </div>
          
          <p className="text-gray-700 leading-relaxed mb-6">
            {t('helpDeskIntro')}
          </p>

          <div className="space-y-4">
            <Link href="https://www.japan.travel/en/plan/hotline/" target="_blank" rel="noopener noreferrer" className="flex flex-col p-4 border-2 border-black rounded-2xl hover:bg-gray-50 transition-colors">
              <span className="font-bold text-black mb-1">{t('link1Title')}</span>
              <span className="text-sm text-blue-600 break-all underline decoration-blue-300 underline-offset-2">https://www.japan.travel/en/plan/hotline/</span>
            </Link>
            
            <Link href="https://www.japan.travel/en/news/JapanSafeTravel/" target="_blank" rel="noopener noreferrer" className="flex flex-col p-4 border-2 border-black rounded-2xl hover:bg-gray-50 transition-colors">
              <span className="font-bold text-black mb-1">{t('link2Title')}</span>
              <span className="text-sm text-blue-600 break-all underline decoration-blue-300 underline-offset-2">https://www.japan.travel/en/news/JapanSafeTravel/</span>
            </Link>
            
            <Link href="https://crisis.yahoo.co.jp/map/" target="_blank" rel="noopener noreferrer" className="flex flex-col p-4 border-2 border-black rounded-2xl hover:bg-gray-50 transition-colors">
              <span className="font-bold text-black mb-1">{t('link3Title')}</span>
              <span className="text-sm text-blue-600 break-all underline decoration-blue-300 underline-offset-2">https://crisis.yahoo.co.jp/map/</span>
            </Link>
            
            <Link href="https://wwwtb.mlit.go.jp/hokkaido/unkoujouhou/index.html" target="_blank" rel="noopener noreferrer" className="flex flex-col p-4 border-2 border-black rounded-2xl hover:bg-gray-50 transition-colors">
              <span className="font-bold text-black mb-1">{t('link4Title')}</span>
              <span className="text-sm text-blue-600 break-all underline decoration-blue-300 underline-offset-2">https://wwwtb.mlit.go.jp/hokkaido/unkoujouhou/index.html</span>
            </Link>
            
            <Link href="https://www.jrhokkaido.co.jp/global/index.html" target="_blank" rel="noopener noreferrer" className="flex flex-col p-4 border-2 border-black rounded-2xl hover:bg-gray-50 transition-colors">
              <span className="font-bold text-black mb-1">{t('link5Title')}</span>
              <span className="text-sm text-blue-600 break-all underline decoration-blue-300 underline-offset-2">https://www.jrhokkaido.co.jp/global/index.html</span>
            </Link>
            
            <Link href="https://www.jrhokkaidobus.com/en/" target="_blank" rel="noopener noreferrer" className="flex flex-col p-4 border-2 border-black rounded-2xl hover:bg-gray-50 transition-colors">
              <span className="font-bold text-black mb-1">{t('link6Title')}</span>
              <span className="text-sm text-blue-600 break-all underline decoration-blue-300 underline-offset-2">https://www.jrhokkaidobus.com/en/</span>
            </Link>
          </div>
        </div>

      </div>
    </div>
  );
}
