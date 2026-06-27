"""Service-oriented ML layer.

Each model is encapsulated in its own service module and loaded exactly once
via the model registry. Services never import one another's heavy state; the
``pipeline`` module orchestrates them.
"""
