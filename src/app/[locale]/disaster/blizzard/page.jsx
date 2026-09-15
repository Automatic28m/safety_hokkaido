import Image from "next/image";
import Link from "next/link";
import Accordion from "@/components/Accordion";
import { getTranslations } from 'next-intl/server';

export default async function BlizzardPage({ params }) {
  const { locale } = await params;
  const t = await getTranslations('Blizzard');

  return (
    <div className="flex flex-col items-center pb-10 bg-[#f4f7f6] pt-24">
      <div className="w-[90%] max-w-md">
        
        {/* Header */}
        <h1 className="font-torsilp text-5xl font-black text-black tracking-wider mb-2">
          {t('title')}
        </h1>
        <div className="border-b-2 border-dashed border-gray-400 mb-6"></div>

        {/* Tabs */}
        <div className="flex gap-0 mb-8">
          <div className="bg-orange-400 text-white font-bold py-2 px-6 rounded-t-xl z-10">
            {t('blizzardTab')}
          </div>
          <Link href={`/${locale}/disaster/earthquake`} className="bg-gray-300 text-gray-700 font-bold py-2 px-6 rounded-t-xl hover:bg-gray-400 transition-colors">
            {t('earthquakeTab')}
          </Link>
        </div>

        {/* Content Box */}
        <div className="bg-white rounded-b-3xl rounded-tl-3xl shadow-md p-6 -mt-8 pt-8 mb-12 relative">
          <h2 className="font-torsilp text-4xl font-black text-black mb-4">{t('blizzardHeading')}</h2>
          
          <div className="relative w-full aspect-[2/1] rounded-xl overflow-hidden mb-6 border-2 border-black">
            <Image 
              src="/illustrations/Blizzard.png" 
              alt="Blizzard Illustration" 
              fill 
              className="object-cover"
            />
          </div>

          <h3 className="text-black text-2xl font-bold border-b-2 border-black pb-1 inline-block mb-3">
            {t('whatIsIt')}
          </h3>
          <p className="text-gray-800 leading-relaxed mb-6" dangerouslySetInnerHTML={{ __html: t.raw('whatIsItDesc') }} />

          <div className="space-y-4 mb-8">
            <Accordion title={t('whatIfItHappens')}>
              <h4 className="font-bold text-lg mb-2">{t('blzNowOutside')}</h4>
              <ul className="list-disc pl-5 space-y-2 mb-4 text-sm opacity-90">
                <li>{t('blzNowOutside1')}</li>
                <li>{t('blzNowOutside2')}</li>
              </ul>
              <h4 className="font-bold text-lg mb-2">{t('blzNowCar')}</h4>
              <ul className="list-disc pl-5 space-y-2 text-sm opacity-90">
                <li>{t('blzNowCar1')}</li>
                <li>{t('blzNowCar2')}</li>
                <li>{t('blzNowCar3')}</li>
              </ul>
            </Accordion>
            
            <Accordion title={t('whatCanHappen')}>
              <p className="font-bold text-base mb-2">{t('blzCanHappenIntro')}</p>
              <ul className="list-none space-y-1 text-sm opacity-90">
                <li>{t('blzCanHappen1')}</li>
                <li>{t('blzCanHappen2')}</li>
                <li>{t('blzCanHappen3')}</li>
              </ul>
            </Accordion>
          </div>

          <h3 className="text-2xl font-bold border-b-2 border-black pb-1 inline-block mb-6 text-black">
            {t('whatIsYourSituation')}
          </h3>

          <div className="space-y-6">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <svg className="text-green-500 w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
                <h4 className="text-xl font-bold text-green-500">{t('hotelRoom')}</h4>
              </div>
              <p className="text-gray-700">{t('hotelRoomDesc')}</p>
            </div>

            <div className="pl-4 border-l-2 border-gray-200 relative">
              <div className="absolute w-3 h-3 bg-green-500 rounded-full -left-[7px] top-1.5"></div>
              <h5 className="text-lg font-bold text-gray-800 mb-1">{t('wantToGoOut')}</h5>
              <p className="text-gray-700 text-sm">{t('wantToGoOutDesc')}</p>
            </div>

            <div>
              <div className="flex items-center gap-2 mb-2 mt-6">
                <svg className="text-green-500 w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4M10 17l5-5-5-5M15 12H3"/></svg>
                <h4 className="text-xl font-bold text-green-500">{t('outside')}</h4>
              </div>
              <p className="text-gray-700">{t('outsideDesc')}</p>
            </div>

            <div className="pl-4 border-l-2 border-gray-200 relative">
              <div className="absolute w-3 h-3 bg-green-500 rounded-full -left-[7px] top-1.5"></div>
              <h5 className="text-lg font-bold text-gray-800 mb-1">{t('cantGetBack')}</h5>
              <p className="text-gray-700 text-sm">{t('cantGetBackDesc')}</p>
            </div>
          </div>
        </div>

        {/* Links Section */}
        <h2 className="font-torsilp text-5xl font-black text-black tracking-wider mb-2">{t('linksTitle')}</h2>
        <div className="border-b-2 border-dashed border-gray-400 mb-6"></div>

        <div className="space-y-4">
          <Link href={`/${locale}/learning-materials`} className="bg-white rounded-2xl p-6 shadow-md flex items-center justify-between group hover:shadow-lg transition-shadow">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <div className="w-3 h-3 rounded-full bg-green-500"></div>
                <h3 className="text-xl font-bold text-black">{t('link1Title')}</h3>
              </div>
              <p className="text-gray-600 text-sm border-t border-gray-200 pt-2 mt-2">{t('link1Desc')}</p>
            </div>
            <div className="w-10 h-10 bg-orange-400 rounded-full flex justify-center items-center text-white shrink-0 group-hover:scale-110 transition-transform">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="m9 18 6-6-6-6"/></svg>
            </div>
          </Link>

          <Link href={`/${locale}/learning-materials`} className="bg-white rounded-2xl p-6 shadow-md flex items-center justify-between group hover:shadow-lg transition-shadow">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <div className="w-3 h-3 rounded-full bg-green-500"></div>
                <h3 className="text-xl font-bold text-black">{t('link2Title')}</h3>
              </div>
              <p className="text-gray-600 text-sm border-t border-gray-200 pt-2 mt-2">{t('link2Desc')}</p>
            </div>
            <div className="w-10 h-10 bg-orange-400 rounded-full flex justify-center items-center text-white shrink-0 group-hover:scale-110 transition-transform">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="m9 18 6-6-6-6"/></svg>
            </div>
          </Link>
        </div>

      </div>
    </div>
  );
}
