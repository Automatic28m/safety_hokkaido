# Agent flow

1. Classify intent as general, RAG, real-time, or RAG plus real-time.
2. Reformulate context-dependent questions and translate for retrieval when required.
3. Invoke only the retrieval and/or data tools allowed by the route.
4. Pass evidence and tool results to the decision layer.
