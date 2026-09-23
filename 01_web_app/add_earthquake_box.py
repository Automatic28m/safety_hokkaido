import re

with open("src/app/[locale]/page.jsx", "r") as f:
    content = f.read()

# Add the fetch logic
fetch_code = """
  // Fetch weather (mock)
  const currentTemp = 24;
  const maxTemp = 24;
  const minTemp = 16;
  const bgGradient = "from-blue-400 to-blue-300"; // Can be dynamic based on real weather

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
"""

content = re.sub(r'  const currentTemp = 24;.*?const bgGradient = "from-blue-400 to-blue-300";.*?\n', fetch_code, content, flags=re.DOTALL)

# Add the earthquake box UI
eq_box = """
      </section>

      {/* Earthquake Card */}
      <section className="w-[90%] max-w-md bg-white rounded-3xl p-6 shadow-xl mt-6 relative z-20">
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
            {/* Decorative waves for earthquake */}
            <div className="absolute right-[-10px] bottom-[-20px] opacity-20">
              <svg width="120" height="120" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M2 12h4l2-9 5 18 3-9h6"/>
              </svg>
            </div>
          </div>
        ) : (
          <div className="bg-gray-200 rounded-2xl p-6 text-gray-500 text-center">
            {t('noEarthquakeData')}
          </div>
        )}
      </section>
"""

content = content.replace('      </section>\n\n      {/* Scroll indicator */}', eq_box + '\n\n      {/* Scroll indicator */}')

with open("src/app/[locale]/page.jsx", "w") as f:
    f.write(content)
