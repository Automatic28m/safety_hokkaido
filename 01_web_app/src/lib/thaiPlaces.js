// Mapbox does not index Thai place names, so Thai input is resolved here first.
// Coordinates are approximate (good enough to drop a pin; the user can drag it).
const PLACES = [
  { th: ['สถานีซัปโปโร'], en: 'Sapporo Station', lat: 43.0687, lng: 141.3508 },
  { th: ['ซัปโปโร', 'ซัพโพโร', 'ซับโปโร'], en: 'Sapporo', lat: 43.0618, lng: 141.3545 },
  { th: ['สนามบินชินชิโตเสะ', 'สนามบินนิวชิโตเสะ', 'ชินชิโตเสะ', 'นิวชิโตเสะ', 'ชิโตเสะ'], en: 'New Chitose Airport', lat: 42.7752, lng: 141.6923 },
  { th: ['สถานีโอตารุ'], en: 'Otaru Station', lat: 43.1971, lng: 140.9945 },
  { th: ['โอตารุ'], en: 'Otaru', lat: 43.1907, lng: 140.9947 },
  { th: ['สถานีฮาโกดาเตะ'], en: 'Hakodate Station', lat: 41.7733, lng: 140.7266 },
  { th: ['สนามบินฮาโกดาเตะ'], en: 'Hakodate Airport', lat: 41.77, lng: 140.8219 },
  { th: ['ฮาโกดาเตะ', 'ฮะโกะดะเตะ'], en: 'Hakodate', lat: 41.7688, lng: 140.7288 },
  { th: ['สถานีอาซาฮิกาวะ'], en: 'Asahikawa Station', lat: 43.764, lng: 142.3585 },
  { th: ['อาซาฮิกาวะ', 'อาซาฮิคาวะ'], en: 'Asahikawa', lat: 43.7706, lng: 142.365 },
  { th: ['ฟุราโนะ'], en: 'Furano', lat: 43.342, lng: 142.383 },
  { th: ['บิเอะ', 'บิเอ'], en: 'Biei', lat: 43.5877, lng: 142.4658 },
  { th: ['นิเซโกะ'], en: 'Niseko', lat: 42.8048, lng: 140.6874 },
  { th: ['โนโบริเบตสึ', 'โนโบริเบทสึ'], en: 'Noboribetsu', lat: 42.4129, lng: 141.1019 },
  { th: ['ทะเลสาบโทยะ', 'โทยะ'], en: 'Lake Toya', lat: 42.595, lng: 140.859 },
  { th: ['คุชิโระ'], en: 'Kushiro', lat: 42.9849, lng: 144.3814 },
  { th: ['อาบาชิริ'], en: 'Abashiri', lat: 44.0206, lng: 144.2733 },
  { th: ['วักกะไน', 'วากคานาอิ'], en: 'Wakkanai', lat: 45.4155, lng: 141.6733 },
  { th: ['รุสึสึ'], en: 'Rusutsu', lat: 42.749, lng: 140.9 },
  { th: ['ชิเรโตโกะ', 'ชิเรโทโกะ'], en: 'Shiretoko', lat: 44.07, lng: 145.09 },
  { th: ['โอบิฮิโระ'], en: 'Obihiro', lat: 42.9236, lng: 143.1983 },
  { th: ['มุโรรัน'], en: 'Muroran', lat: 42.3152, lng: 140.9738 },
  { th: ['โทมาโกไม'], en: 'Tomakomai', lat: 42.6342, lng: 141.6055 },
  { th: ['คิตามิ'], en: 'Kitami', lat: 43.803, lng: 143.8944 },
  { th: ['โจซังเก', 'โจซังเคย์'], en: 'Jozankei', lat: 42.969, lng: 141.165 },
  { th: ['ซูซูกิโนะ'], en: 'Susukino', lat: 43.0556, lng: 141.3537 },
  { th: ['สวนโอโดริ', 'โอโดริ'], en: 'Odori Park', lat: 43.06, lng: 141.347 },
];

export const hasThai = (s) => /[\u0E00-\u0E7F]/.test(s || '');

// Whole word contained in the input, or the input is the start of a known name (autocomplete while typing)
export function lookupThai(q) {
  const norm = (q || '').replace(/\s+/g, '');
  if (norm.length < 2) return [];
  const hits = [];
  for (const p of PLACES) {
    let best = 0;
    for (const v of p.th) {
      if (norm.includes(v) || v.startsWith(norm)) best = Math.max(best, v.length);
    }
    if (best) hits.push({ p, best });
  }
  return hits
    .sort((a, b) => b.best - a.best)
    .slice(0, 5)
    .map(({ p }) => ({ id: `th-${p.en}`, text: p.en, place_name: `${p.en}, Hokkaido, Japan`, lat: p.lat, lng: p.lng }));
}
