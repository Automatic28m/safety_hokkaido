import Image from "next/image";
import Link from "next/link";
import Accordion from "@/components/Accordion";
import { getTranslations } from 'next-intl/server';

export default async function EarthquakePage({ params }) {
  const { locale } = await params;
  const t = await getTranslations('Earthquake');
  const tBlizzard = await getTranslations('Blizzard');

  return (
    <div className="flex flex-col items-center pb-10 bg-[#f4f7f6] pt-45">
      <div className="w-[90%] max-w-md md:max-w-5xl lg:max-w-6xl">
        
        {/* Header */}
        <h1 className="font-torsilp text-5xl md:text-8xl font-black text-black tracking-wider mb-2 md:mb-6 uppercase">
          {t('title')}
        </h1>
        <div className="border-b-2 border-dashed border-gray-400 mb-6 md:mb-10"></div>

        {/* Tabs */}
        <div className="flex gap-0 mb-8">
          <Link href={`/${locale}/disaster/blizzard`} className="bg-gray-300 text-gray-700 font-bold py-2 px-6 rounded-t-xl hover:bg-gray-400 transition-colors">
            {tBlizzard('blizzardTab')}
          </Link>
          <div className="bg-orange-400 text-white font-bold py-2 px-6 rounded-t-xl z-10">
            {tBlizzard('earthquakeTab')}
          </div>
        </div>

        {/* Content Box (Earthquake & Tsunami on Mobile, Just Earthquake on Desktop) */}
        <div className="bg-white rounded-tr-3xl rounded-b-none md:rounded-tr-[32px] shadow-md p-6 md:p-10 -mt-8 pt-8 md:pt-12 relative">
          
          {/* Earthquake Title and Banner */}
          <h2 className="font-torsilp text-4xl md:text-6xl font-black text-black mb-4">{t('earthquakeHeading')}</h2>
          
          <div className="relative w-full aspect-[2/1] md:aspect-[3/1] rounded-xl overflow-hidden mb-8 md:mb-10 border-2 border-black">
            <Image
              src="/illustrations/Earthquake .png"
              alt="Earthquake Illustration"
              fill
              className="object-cover"
            />
          </div>

          <div className="md:grid md:grid-cols-2 md:gap-12">
            <div>
              <h3 className="text-2xl font-bold border-b-2 text-black border-black pb-1 inline-block mb-3">
                {tBlizzard('whatIsIt')}
              </h3>
              <p className="text-gray-800 leading-relaxed mb-6" dangerouslySetInnerHTML={{ __html: t.raw('whatIsItDesc') }} />

              <div className="space-y-4 mb-10">
                <Accordion title={tBlizzard('whatIfItHappens')}>
                  <h4 className="font-bold text-lg mb-2">{t('eqNowWhile')}</h4>
                  <ul className="list-disc pl-5 space-y-1 mb-4 text-sm opacity-90">
                    <li>{t('eqNowWhile1')}</li>
                    <li>{t('eqNowWhile2')}</li>
                    <li>{t('eqNowWhile3')}</li>
                  </ul>
                  <h4 className="font-bold text-lg mb-2">{t('eqNowWhen')}</h4>
                  <ul className="list-disc pl-5 space-y-1 text-sm opacity-90">
                    <li>{t('eqNowWhen1')}</li>
                    <li>{t('eqNowWhen2')}</li>
                    <li>{t('eqNowWhen3')}</li>
                  </ul>
                </Accordion>
                
                <Accordion title={tBlizzard('whatCanHappen')}>
                  <p className="font-bold text-base mb-2">{t('eqCanHappenIntro')}</p>
                  <ul className="list-none space-y-1 text-sm opacity-90">
                    <li>{t('eqCanHappen1')}</li>
                    <li>{t('eqCanHappen2')}</li>
                    <li>{t('eqCanHappen3')}</li>
                  </ul>
                </Accordion>
              </div>
            </div>

            <div>
              <h3 className="text-3xl font-black text-black tracking-wider mb-4">
                {t('shakingLevels')}
              </h3>

              <div className="space-y-3 mb-12">
                <div className="border-2 border-black rounded-2xl p-3 flex justify-between items-center bg-white shadow-sm">
                  <div>
                    <h4 className="text-black font-bold text-lg">{t('level1Title')}</h4>
                    <p className="text-gray-600 text-sm">{t('level1Desc')}</p>
                  </div>
                  <div className="bg-green-500 text-white font-bold text-xs py-2 px-4 rounded-xl text-center w-24" dangerouslySetInnerHTML={{ __html: t.raw('level1Badge') }} />
                </div>

                <div className="border-2 border-black rounded-2xl p-3 flex justify-between items-center bg-white shadow-sm">
                  <div>
                    <h4 className="text-black font-bold text-lg">{t('level2Title')}</h4>
                    <p className="text-gray-600 text-sm" dangerouslySetInnerHTML={{ __html: t.raw('level2Desc') }} />
                  </div>
                  <div className="bg-orange-400 text-white font-bold text-xs py-2 px-4 rounded-xl text-center w-24" dangerouslySetInnerHTML={{ __html: t.raw('level2Badge') }} />
                </div>

                <div className="border-2 border-black rounded-2xl p-3 flex justify-between items-center bg-white shadow-sm">
                  <div>
                    <h4 className="text-black font-bold text-lg">{t('level3Title')}</h4>
                    <p className="text-gray-600 text-sm">{t('level3Desc')}</p>
                  </div>
                  <div className="bg-red-500 text-white font-bold text-xs py-2 px-4 rounded-xl text-center w-24" dangerouslySetInnerHTML={{ __html: t.raw('level3Badge') }} />
                </div>

                <div className="border-2 border-black rounded-2xl p-3 flex justify-between items-center bg-white shadow-sm">
                  <div>
                    <h4 className="text-black font-bold text-lg">{t('level4Title')}</h4>
                    <p className="text-gray-600 text-sm" dangerouslySetInnerHTML={{ __html: t.raw('level4Desc') }} />
                  </div>
                  <div className="bg-purple-600 text-white font-bold text-xs py-2 px-4 rounded-xl text-center w-24" dangerouslySetInnerHTML={{ __html: t.raw('level4Badge') }} />
                </div>
              </div>
            </div>
          </div>
          
          {/* Mobile Tsunami separator (hidden on desktop since it will break out) */}
          <div className="md:hidden relative mt-12">
            <div className="absolute left-6 top-[-30px] border-l-2 border-dashed border-gray-400 h-16"></div>
            <div className="absolute left-10 top-[-30px] bg-[#0047b3] text-white text-sm font-bold py-2 px-4 rounded-r-xl rounded-bl-xl shadow-md w-64">
              <span dangerouslySetInnerHTML={{ __html: t.raw('tsunamiBanner') }} />
              <div className="absolute w-3 h-3 bg-[#0047b3] rotate-45 -left-1.5 top-3"></div>
            </div>
          </div>
        </div>

        {/* Tsunami Section (Broken out on desktop, flows from previous div on mobile) */}
        <div className="md:mt-12 bg-white md:bg-transparent rounded-b-3xl md:rounded-none shadow-md md:shadow-none p-6 md:p-0 pt-0 md:pt-0 relative z-0 md:z-auto md:mb-12">
          
          {/* Desktop Tsunami separator */}
          <div className="hidden md:block relative h-24 w-full">
            <div className="absolute left-4 top-[-20px] border-l-2 border-dashed border-gray-400 h-16 z-0"></div>
            <div className="absolute left-8 top-[-10px] bg-[#0047b3] text-white text-sm font-bold py-2 px-4 rounded-r-xl rounded-bl-xl shadow-md w-[280px] z-10">
              <span dangerouslySetInnerHTML={{ __html: t.raw('tsunamiBanner') }} />
              <div className="absolute w-3 h-3 bg-[#0047b3] rotate-45 -left-1.5 top-3"></div>
            </div>
          </div>

          <div className="pt-16 md:pt-0">
            <h2 className="font-torsilp text-4xl md:text-6xl font-black text-black mb-4">{t('tsunamiHeading')}</h2>
            <div className="relative w-full aspect-[2/1] md:aspect-[3/1] rounded-xl overflow-hidden mb-8 md:mb-10 border-2 border-black">
              <Image
                src="/illustrations/Tsunami.png"
                alt="Tsunami Illustration"
                fill
                className="object-cover"
              />
            </div>

            <div className="md:grid md:grid-cols-2 md:gap-12">
              <div>
                <h3 className="text-2xl font-bold border-b-2 border-black pb-1 inline-block mb-3 text-black">
                  {tBlizzard('whatIsIt')}
                </h3>
                <p className="text-gray-800 leading-relaxed mb-6" dangerouslySetInnerHTML={{ __html: t.raw('tsunamiWhatIsItDesc') }} />
              </div>

              <div>
                <div className="space-y-4 mb-4">
                  <Accordion title={tBlizzard('whatIfItHappens')}>
                    <ul className="list-disc pl-5 space-y-2 text-sm opacity-90">
                      <li>{t('tsNow1')}</li>
                      <li>{t('tsNow2')}</li>
                      <li>{t('tsNow3')}</li>
                      <li>{t('tsNow4')}</li>
                    </ul>
                  </Accordion>
                  
                  <Accordion title={tBlizzard('whatCanHappen')}>
                    <p className="font-bold text-base mb-2">{t('tsCanHappenIntro')}</p>
                    <ul className="list-none space-y-1 text-sm opacity-90">
                      <li>{t('tsCanHappen1')}</li>
                      <li>{t('tsCanHappen2')}</li>
                      <li>{t('tsCanHappen3')}</li>
                    </ul>
                  </Accordion>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Links Section */}
        <h2 className="font-torsilp text-5xl md:text-7xl font-black text-black tracking-wider mb-2 mt-12">{tBlizzard('linksTitle')}</h2>
        <div className="border-b-2 border-dashed border-gray-400 mb-6 md:mb-10"></div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-8 mb-10">
          <Link href={`/${locale}/learning-materials`} className="bg-white rounded-2xl p-6 shadow-md flex items-center justify-between group hover:shadow-lg transition-shadow">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <div className="w-3 h-3 rounded-full bg-green-500"></div>
                <h3 className="text-xl font-bold text-black">{t('link1Title')}</h3>
              </div>
              <p className="text-gray-600 text-sm border-t border-gray-200 pt-2 mt-2">{t('link1Desc')}</p>
            </div>
            <div className="w-10 h-10 bg-orange-400 rounded-full flex justify-center items-center text-white shrink-0 group-hover:scale-110 transition-transform">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="m9 18 6-6-6-6" /></svg>
            </div>
          </Link>
        </div>

      </div>
    </div>
  );
}
