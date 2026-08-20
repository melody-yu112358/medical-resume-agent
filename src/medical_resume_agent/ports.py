from typing import Protocol


class ModelGateway(Protocol):
    def generate(self, *, task: str, context: dict[str, object]) -> str: ...
