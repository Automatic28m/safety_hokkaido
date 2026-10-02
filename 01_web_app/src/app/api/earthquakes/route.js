import { NextResponse } from 'next/server';
import { getLatestQuake, parseCoords } from '@/lib/liveData';

// GET /api/earthquakes            -> latest quake in the Hokkaido area
// GET /api/earthquakes?lat=&lng=  -> same, plus distance_km from that point
export async function GET(req) {
  try {
    return NextResponse.json(await getLatestQuake(parseCoords(req.nextUrl.searchParams)));
  } catch (err) {
    console.warn('Earthquake API error:', err.message);
    return NextResponse.json({ error: 'earthquake_unavailable' }, { status: 502 });
  }
}
