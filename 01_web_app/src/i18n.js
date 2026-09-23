import {notFound} from 'next/navigation';
import {getRequestConfig} from 'next-intl/server';
 
const locales = ['en', 'th'];
 
export default getRequestConfig(async ({requestLocale}) => {
  let locale = await requestLocale;
  console.log("I18N LOADED LOCALE:", locale);
  if (!locales.includes(locale)) notFound();
 
  return {
    locale,
    messages: (await import(`../messages/${locale}.json`)).default
  };
});
