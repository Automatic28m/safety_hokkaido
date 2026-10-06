import React from 'react';

export default function RightPanel({ tabs, activeTabId, setActiveTabId, isPanelCollapsed, setIsPanelCollapsed, closeTab, liveSources = [] }) {
  if (tabs.length === 0) return null;

  const activeTab = tabs.find(t => t.id === activeTabId);

  const getGoogleMapsUrl = (origin, destination, mode) => {
    let travelMode = 'transit';
    if (mode === 'car') travelMode = 'driving';
    if (mode === 'bus') travelMode = 'transit';
    const encOrigin = encodeURIComponent(origin);
    const encDest = encodeURIComponent(destination);
    return `https://www.google.com/maps/dir/?api=1&origin=${encOrigin}&destination=${encDest}&travelmode=${travelMode}`;
  };

  return (
    <div 
        className={`transition-all duration-300 ease-in-out flex flex-col bg-white overflow-hidden relative md:border-l border-gray-200 shrink-0 ${isPanelCollapsed ? 'h-14 md:h-full w-full md:w-12 cursor-pointer hover:bg-gray-50' : 'h-[45vh] md:h-full w-full md:w-1/2'}`}
        onClick={isPanelCollapsed ? () => setIsPanelCollapsed(false) : undefined}
    >
      {isPanelCollapsed ? (
          <div className="h-full w-full flex items-center justify-center relative">
            <div className="md:-rotate-90 whitespace-nowrap text-blue-600 font-bold flex items-center gap-2 tracking-wide">
                📊 Open Panel
            </div>
          </div>
      ) : (
          <>
            {/* Tab Bar */}
            <div className="flex bg-gray-100 overflow-x-auto shrink-0 border-b border-gray-200">
              {tabs.map((tab) => (
                <div 
                  key={tab.id}
                  onClick={() => setActiveTabId(tab.id)}
                  className={`flex items-center gap-2 px-4 py-3 border-r border-gray-200 cursor-pointer min-w-max transition-colors ${activeTabId === tab.id ? 'bg-white font-bold border-b-2 border-b-blue-600' : 'hover:bg-gray-200'}`}
                >
                  <span className="text-sm">
                    {tab.type === 'map' ? '🗺️ Map' : tab.type === 'weather_forecast' ? '⛅ Weather' : '✈️ Flights'}
                  </span>
                  <button 
                    onClick={(e) => { e.stopPropagation(); closeTab(tab.id); }}
                    className="text-gray-400 hover:text-red-500 rounded-full p-1"
                    title="Close"
                  >
                    ×
                  </button>
                </div>
              ))}
              
              <div className="ml-auto flex items-center px-2">
                <button 
                    onClick={() => setIsPanelCollapsed(true)}
                    className="w-8 h-8 flex items-center justify-center rounded-full hover:bg-gray-200 text-gray-500 hover:text-gray-800 transition-colors rotate-90 md:rotate-0"
                    title="Minimize"
                >
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M9 18l6-6-6-6" /></svg>
                </button>
              </div>
            </div>

            {/* Content Area */}
            {activeTab && (
              <div className="flex-1 w-full relative bg-gray-50 flex flex-col overflow-hidden">
                <div className="bg-blue-50 py-1.5 px-4 text-xs font-semibold text-blue-800 border-b border-blue-100 flex justify-between shrink-0">
                  <span>Data snapshot for this request</span>
                  <span>Generated at {activeTab.timestamp}</span>
                </div>
                
                {activeTab.type === 'map' && (
                  <div className="flex flex-col h-full">
                      <div className="p-4 flex justify-between items-center shrink-0">
                        <div className="flex flex-col gap-2">
                          <h3 className="font-bold text-[#0c4ca3] text-lg flex items-center gap-2">
                            📍 {activeTab.payload.origin} ➔ {activeTab.payload.destination}
                            <span className="text-gray-500 text-sm ml-2 bg-gray-200 px-2 py-1 rounded-full flex items-center gap-1">
                              {activeTab.payload.mode === 'train' ? '🚆' : activeTab.payload.mode === 'bus' ? '🚌' : activeTab.payload.mode === 'walk' ? '🚶' : '🚗'} {activeTab.payload.mode}
                            </span>
                          </h3>
                          <a 
                            href={getGoogleMapsUrl(activeTab.payload.origin, activeTab.payload.destination, activeTab.payload.mode)}
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="bg-blue-600 text-white px-4 py-2 w-fit rounded-full shadow hover:bg-blue-700 text-sm font-semibold flex items-center gap-2 transition-colors"
                          >
                            🗺️ Open in App
                          </a>
                        </div>
                      </div>
                      <iframe
                          title="Route Map"
                          src={`https://maps.google.com/maps?saddr=${encodeURIComponent(activeTab.payload.origin)}&daddr=${encodeURIComponent(activeTab.payload.destination)}&dirflg=${activeTab.payload.mode === 'train' || activeTab.payload.mode === 'bus' ? 'r' : activeTab.payload.mode === 'walk' ? 'w' : 'd'}&output=embed`}
                          className="w-full h-full border-none"
                          loading="lazy"
                      />
                  </div>
                )}
                
                {activeTab.type === 'weather_forecast' && (
                  <div className="flex flex-col p-6 h-full overflow-y-auto">
                      <h2 className="text-2xl font-bold text-gray-800 mb-4">⛅ Hourly Weather: {activeTab.payload.location}</h2>
                      <p className="text-gray-500 mb-6 text-sm">Visual timeline of temperature and conditions.</p>
                      
                      <div className="flex-1 rounded-2xl flex flex-col bg-white text-gray-700">
                          {(() => {
                              const weatherData = liveSources.find(s => s.provider === 'meteosource')?.data?.hourly_forecast || [];
                              if (weatherData.length === 0) return <div className="p-4 text-center text-gray-400 border-2 border-dashed border-gray-300 rounded-xl">No hourly data available.</div>;
                              return (
                                  <div className="flex overflow-x-auto gap-4 pb-4 px-2 pt-2 snap-x">
                                      {weatherData.map((h, i) => {
                                          const t = new Date(h.time_utc);
                                          const timeStr = t.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                                          return (
                                              <div key={i} className="flex flex-col items-center bg-gray-50 rounded-xl p-4 min-w-[100px] border border-gray-100 shadow-sm snap-start">
                                                  <span className="font-bold text-sm text-gray-500 mb-2">{timeStr}</span>
                                                  <span className="text-2xl font-bold text-blue-900">{h.temperature_c}°</span>
                                                  <span className="text-xs text-center mt-2 text-gray-600 leading-tight">{h.summary}</span>
                                              </div>
                                          );
                                      })}
                                  </div>
                              );
                          })()}
                      </div>
                  </div>
                )}
                
                {activeTab.type === 'flight_board' && (
                  <div className="flex flex-col h-full bg-gray-900 text-white font-mono">
                      <div className="p-4 border-b border-gray-700 shrink-0">
                          <h2 className="text-xl font-bold text-yellow-400">✈️ FLIGHT STATUS BOARD</h2>
                          <p className="text-gray-400 text-sm">{activeTab.payload.airport} - {activeTab.payload.direction.toUpperCase()}</p>
                      </div>
                      <div className="flex-1 overflow-y-auto p-4">
                          <table className="w-full text-left border-collapse">
                              <thead>
                                  <tr className="text-gray-400 border-b border-gray-700 text-sm">
                                      <th className="pb-2">FLIGHT</th>
                                      <th className="pb-2">TIME</th>
                                      <th className="pb-2">STATUS</th>
                                  </tr>
                              </thead>
                              <tbody>
                                  {(() => {
                                      const flightData = liveSources.find(s => s.provider === 'aviationstack')?.data?.flights || [];
                                      if (flightData.length === 0) return <tr><td colSpan="3" className="py-4 text-center text-gray-500">No flight data available.</td></tr>;
                                      return flightData.map((f, i) => {
                                          const timeStr = f.estimated_time || f.scheduled_time;
                                          const t = timeStr ? new Date(timeStr).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'N/A';
                                          const statusColor = f.flight_status === 'active' || f.flight_status === 'scheduled' ? 'text-green-400' : f.flight_status === 'cancelled' ? 'text-gray-500' : 'text-red-400';
                                          return (
                                              <tr key={i} className="border-b border-gray-800/50 hover:bg-gray-800 text-sm">
                                                  <td className="py-3">
                                                      <span className="font-bold">{f.flight_number || 'UNKNOWN'}</span>
                                                      <br/><span className="text-xs text-gray-500">{f.airline}</span>
                                                  </td>
                                                  <td className="py-3">{t}</td>
                                                  <td className={`py-3 font-bold ${statusColor}`}>{f.flight_status.toUpperCase()}</td>
                                              </tr>
                                          );
                                      });
                                  })()}
                              </tbody>
                          </table>
                      </div>
                  </div>
                )}
              </div>
            )}
          </>
      )}
    </div>
  );
}
