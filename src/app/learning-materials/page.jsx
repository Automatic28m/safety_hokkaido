import Link from "next/link";

export default function LearningMaterialsPage() {
  return (
    <div className="flex flex-col items-center pb-10 bg-[#f4f7f6] pt-24">
      <div className="w-[90%] max-w-md">
        
        {/* Header */}
        <h1 className="font-bowlby text-5xl font-black text-black tracking-tighter mb-2 leading-none uppercase">
          LEARNING<br/>MATERIALS
        </h1>
        <div className="border-b-2 border-dashed border-gray-400 mb-8"></div>

        {/* Section 1: Alerts */}
        <div id="alerts" className="bg-white rounded-3xl shadow-md p-6 mb-6 scroll-mt-32">
          <h2 className="text-2xl font-bold text-black mb-4 leading-tight">
            What are weather and disaster alerts?
          </h2>
          <p className="text-gray-700 leading-relaxed mb-6">
            In Japan, the Japan Meteorological Agency (JMA) issues official alerts when dangerous weather or a disaster is expected. They tell you how serious the situation is, so you can decide what to do. Alerts come in levels, and the stronger the word, the more dangerous the situation.
          </p>

          <div className="flex items-center gap-2 mb-2">
            <div className="w-3 h-3 rounded-full bg-green-500 shrink-0"></div>
            <h3 className="text-xl font-bold text-black">The main levels</h3>
          </div>
          <p className="text-gray-700 mb-4">Alerts generally rise through three stages.</p>

          <div className="space-y-4">
            {/* Level 1 */}
            <div className="border-2 border-black rounded-2xl p-4">
              <div className="flex justify-between items-start mb-3">
                <h4 className="font-bold text-lg text-black leading-tight">
                  Advisory /<br/>注意報 (chuiho)
                </h4>
                <div className="bg-green-500 text-white font-bold text-sm py-1 px-3 rounded-lg shrink-0">
                  Level: 1
                </div>
              </div>
              <div className="border-b-2 border-dashed border-gray-300 mb-3"></div>
              <p className="text-gray-700 text-sm">
                Conditions could cause minor problems.<br/>
                → Stay aware and check updates.
              </p>
            </div>

            {/* Level 2 */}
            <div className="border-2 border-black rounded-2xl p-4">
              <div className="flex justify-between items-start mb-3">
                <h4 className="font-bold text-lg text-black leading-tight">
                  Warning /<br/>警報 (keiho)
                </h4>
                <div className="bg-orange-400 text-white font-bold text-sm py-1 px-3 rounded-lg shrink-0">
                  Level: 2
                </div>
              </div>
              <div className="border-b-2 border-dashed border-gray-300 mb-3"></div>
              <p className="text-gray-700 text-sm">
                Dangerous conditions are expected.<br/>
                → Avoid unnecessary travel.
              </p>
            </div>

            {/* Level 3 */}
            <div className="border-2 border-black rounded-2xl p-4">
              <div className="flex justify-between items-start mb-3">
                <h4 className="font-bold text-lg text-black leading-tight">
                  Emergency Warning /<br/>特別警報 (tokubetsu keiho)
                </h4>
                <div className="bg-red-600 text-white font-bold text-sm py-1 px-3 rounded-lg shrink-0">
                  Level: 3
                </div>
              </div>
              <div className="border-b-2 border-dashed border-gray-300 mb-3"></div>
              <p className="text-gray-700 text-sm">
                Used for rare, extreme events.<br/>
                → Act now to protect yourself.
              </p>
            </div>
          </div>
        </div>

        {/* Section 2: Power Outages */}
        <div id="power-outages" className="bg-white rounded-3xl shadow-md p-6 mb-10 scroll-mt-32">
          <div className="flex items-center gap-2 mb-4">
            <svg className="text-green-500 w-6 h-6 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M11 20.03c-5.5-.32-10-4.9-10-10.45 0-5.78 4.7-10.46 10.48-10.46 5.78 0 10.46 4.68 10.46 10.46 0 5.55-4.5 10.13-10 10.45"/><path d="m11 2-2 9h4l-2 9"/></svg>
            <h2 className="text-2xl font-bold text-black">Power outages</h2>
          </div>
          
          <p className="text-gray-700 leading-relaxed mb-6">
            Earthquakes and heavy snow can both cut the power, sometimes across a wide area. In 2018, a large earthquake left almost all of Hokkaido without electricity. In winter, a power outage is especially serious because it also stops the heating — staying warm becomes a safety issue, not just a comfort one.
          </p>

          <div className="flex items-center gap-2 mb-2">
            <div className="w-3 h-3 rounded-full bg-green-500 shrink-0"></div>
            <h3 className="text-xl font-bold text-black">Prepare in advance</h3>
          </div>
          <div className="text-gray-700 mb-6 space-y-2 pl-5">
            <p>Keep your phone charged and carry a power bank.</p>
            <p>Have some cash — cards and ATMs may not work.</p>
            <p>Keep a flashlight or light source handy.</p>
          </div>

          <div className="flex items-center gap-2 mb-2">
            <div className="w-3 h-3 rounded-full bg-green-500 shrink-0"></div>
            <h3 className="text-xl font-bold text-black">If the power goes out</h3>
          </div>
          <div className="text-gray-700 space-y-2 pl-5">
            <p>Check official information (JMA, NHK WORLD, the Safety tips app) for updates.</p>
            <p>Save your phone battery, but keep it on for alerts.</p>
            <p>If your room becomes unsafe, move to a designated shelter or a large public facility.</p>
          </div>
        </div>
        <div id="links" className="scroll-mt-32"></div>

      </div>
    </div>
  );
}
