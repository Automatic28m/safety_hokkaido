# Request flow

1. A traveler selects a locale and asks a question through `ChatBot.jsx`.
2. The Next.js route at `src/app/api/chat/route.js` validates and proxies the request.
3. The backend returns a grounded reply for presentation to the traveler.

