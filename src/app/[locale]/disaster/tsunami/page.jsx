import { getTranslations } from 'next-intl/server';

export default async function TsunamiPage({ params }) {
  const { locale } = await params;
  const t = await getTranslations('Tsunami');
  return <div className="p-8 pt-24 min-h-screen text-center"><h1 className="text-3xl font-bold">{t('title')}</h1><p className="mt-4">{t('desc')}</p></div>;
}
