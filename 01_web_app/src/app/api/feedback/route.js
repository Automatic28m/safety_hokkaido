const BACKEND_URL = process.env.BACKEND_API_URL || 'http://localhost:8000';

export async function POST(request) {
  let body;
  try {
    body = await request.json();
  } catch {
    return Response.json({ error: 'invalid_json' }, { status: 400 });
  }
  const { conversation_id, message_id, rating } = body ?? {};
  if (!conversation_id || !message_id || !['up', 'down'].includes(rating)) {
    return Response.json({ error: 'invalid_request' }, { status: 400 });
  }
  // Dev-only: same switch as the chat route
  if (process.env.MOCK_BACKEND === 'true') return Response.json({ ok: true });
  try {
    const upstream = await fetch(`${BACKEND_URL}/api/feedback`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ conversation_id, message_id, rating }),
    });
    return new Response(await upstream.text(), { status: upstream.status, headers: { 'Content-Type': 'application/json' } });
  } catch {
    return Response.json({ error: 'backend_unavailable' }, { status: 503 });
  }
}
