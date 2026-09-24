"""Exceptions shared across the HTTP boundary with node 03."""


class PipelineUnavailableError(Exception):
    """Raise this from node 03 when the pipeline cannot produce an answer right now.

    node 02 maps it to HTTP 503 with a safe, bilingual reply.
    """
