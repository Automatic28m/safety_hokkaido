import Image from "next/image";
import Link from "next/link";
import { getTranslations } from 'next-intl/server';

export default async function TrainPage({ params }) {
  const { locale } = await params;
  const tTrans = await getTranslations('Transportation');
  const t = await getTranslations('Train');

  return (
    <div className="flex flex-col items-center pb-10 bg-[#f4f7f6] pt-24 ">
      <div className="w-[90%] max-w-md md:max-w-5xl lg:max-w-6xl">

        {/* Header */}
        <h1 className="font-torsilp text-5xl font-black text-black tracking-wider mb-2 leading-none uppercase" dangerouslySetInnerHTML={{ __html: tTrans.raw('title') }} />
        <div className="border-b-2 border-dashed border-gray-400 mb-6"></div>

        {/* Tabs */}
        <div className="flex gap-0 mb-8">
          <div className="bg-orange-400 text-white font-bold py-2 px-6 rounded-t-xl z-10 flex-1 text-center">
            {tTrans('trainTab')}
          </div>
          <Link href={`/${locale}/transportation/bus`} className="bg-gray-300 text-gray-700 font-bold py-2 px-6 rounded-t-xl hover:bg-gray-400 transition-colors flex-1 text-center">
            {tTrans('busTab')}
          </Link>
          <Link href={`/${locale}/transportation/car`} className="bg-gray-300 text-gray-700 font-bold py-2 px-4 rounded-t-xl z-10 flex-1 text-center whitespace-nowrap">
            {tTrans('carTab')}
          </Link>
        </div>

        {/* Content Box */}
        <div className="bg-white rounded-b-3xl shadow-md p-6 -mt-8 pt-8 mb-12">
          <h2 className="font-torsilp text-4xl font-black text-black mb-4 uppercase">{t('title')}</h2>

          <div className="relative w-full aspect-[2/1] rounded-xl overflow-hidden mb-6 border-2 border-black bg-orange-400">
            <Image
              src="/illustrations/Train.png"
              alt="Train Illustration"
              fill
              className="object-contain p-2"
            />
          </div>

          <div className="relative mb-6">
            <div className="inline-block bg-[#0047b3] text-white font-bold py-1.5 px-4 rounded-md text-lg">
              {tTrans('howToRide')}
            </div>
            {/* Tooltip triangle */}
            <div className="absolute w-3 h-3 bg-[#0047b3] rotate-45 left-6 -bottom-1"></div>
          </div>

          {/* Timeline Steps */}
          <div className="relative pl-8 space-y-8 mt-8">
            {/* Vertical dashed line */}
            <div className="absolute left-2 top-6 bottom-6 w-px border-l-2 border-dashed border-gray-300"></div>

            {/* Step 1 */}
            <div className="relative">
              <div className="absolute -left-12 bg-white border-2 border-black rounded-full w-12 h-12 flex justify-center items-center z-10">
                <Image src="/icons/ticket.svg" width={24} height={24} alt="icon" />
              </div>
              <h3 className="ml-4 text-blue-700 font-bold text-sm tracking-widest mb-0.5">{t('step1')}</h3>
              <h4 className="ml-4 text-xl font-bold text-black border-b border-gray-300 pb-1 mb-2 inline-block w-full">{t('step1Title')}</h4>
              <p className="ml-4 text-gray-700 text-sm">
                {t('step1Desc')}
              </p>
            </div>

            {/* Step 2 */}
            <div className="relative">
              <div className="absolute -left-12 bg-white border-2 border-black rounded-full w-12 h-12 flex justify-center items-center z-10">
                <Image src="/icons/door-enter.svg" width={24} height={24} alt="icon" />
              </div>
              <h3 className="ml-4 text-blue-700 font-bold text-sm tracking-widest mb-0.5">{t('step2')}</h3>
              <h4 className="ml-4 text-xl font-bold text-black border-b border-gray-300 pb-1 mb-2 inline-block w-full">{t('step2Title')}</h4>
              <p className="ml-4 text-gray-700 text-sm">
                {t('step2Desc')}
              </p>
            </div>

            {/* Step 3 */}
            <div className="relative">
              <div className="absolute -left-12 bg-white border-2 border-black rounded-full w-12 h-12 flex justify-center items-center z-10">
                <Image src="/icons/train.svg" width={24} height={24} alt="icon" />
              </div>
              <h3 className="ml-4 text-blue-700 font-bold text-sm tracking-widest mb-0.5">{t('step3')}</h3>
              <h4 className="ml-4 text-xl font-bold text-black border-b border-gray-300 pb-1 mb-2 inline-block w-full">{t('step3Title')}</h4>
              <p className="ml-4 text-gray-700 text-sm">
                {t('step3Desc')}
              </p>
            </div>

            {/* Step 4 */}
            <div className="relative">
              <div className="absolute -left-12 bg-white border-2 border-black rounded-full w-12 h-12 flex justify-center items-center z-10">
                <Image src="/icons/door-exit.svg" width={24} height={24} alt="icon" />
              </div>
              <h3 className="ml-4 text-blue-700 font-bold text-sm tracking-widest mb-0.5">{t('step4')}</h3>
              <h4 className="ml-4 text-xl font-bold text-black border-b border-gray-300 pb-1 mb-2 inline-block w-full">{t('step4Title')}</h4>
              <p className="ml-4 text-gray-700 text-sm">
                {t('step4Desc')}
              </p>
            </div>
          </div>
        </div>

        {/* Links Section */}
        <h2 className="font-torsilp text-5xl font-black text-black tracking-wider mb-2">{tTrans('links')}</h2>
        <div className="border-b-2 border-dashed border-gray-400 mb-6"></div>

        <div className="space-y-4 mb-10">
          <Link href={`/${locale}/learning-materials`} className="bg-white rounded-2xl p-6 shadow-md flex items-center justify-between group hover:shadow-lg transition-shadow">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <div className="w-3 h-3 rounded-full bg-green-500 shrink-0"></div>
                <h3 className="text-lg font-bold text-black leading-tight">Hokkaido District Transport Bureau</h3>
              </div>
              <p className="text-gray-600 text-sm border-t border-gray-200 pt-2 mt-2">Public Transportation Service Updates in Hokkaido</p>
            </div>
            <div className="w-10 h-10 bg-orange-400 rounded-full flex justify-center items-center text-white shrink-0 group-hover:scale-110 transition-transform ml-2">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="m9 18 6-6-6-6" /></svg>
            </div>
          </Link>

          <Link href={`/${locale}/learning-materials`} className="bg-white rounded-2xl p-6 shadow-md flex items-center justify-between group hover:shadow-lg transition-shadow">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <div className="w-3 h-3 rounded-full bg-green-500 shrink-0"></div>
                <h3 className="text-lg font-bold text-black leading-tight">{t('link2Title')}</h3>
              </div>
              <p className="text-gray-600 text-sm border-t border-gray-200 pt-2 mt-2">{t('link2Desc')}</p>
            </div>
            <div className="w-10 h-10 bg-orange-400 rounded-full flex justify-center items-center text-white shrink-0 group-hover:scale-110 transition-transform ml-2">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="m9 18 6-6-6-6" /></svg>
            </div>
          </Link>
        </div>

      </div>
    </div>
  );
}
