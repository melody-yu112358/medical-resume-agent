from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from ..ports.repositories import ModelGateway


@dataclass(frozen=True)
class GatewayConfig:
    provider: str = "deterministic"
    provider_model: str | None = None
    api_base: str | None = None
    api_key: str | None = None
    temperature: float = 0.0


class DeterministicFallbackGateway(ModelGateway):
    """Safe offline fallback used in tests / CI."""

    def generate(self, *, task: str, context: dict[str, object]) -> str:
        evidence = context.get("evidence") or []
        items = []
        if isinstance(evidence, list):
            for item in evidence:
                if not isinstance(item, dict):
                    continue
                requirement_id = str(item.get("requirement_id", "")).strip()
                requirement = str(item.get("requirement", "")).strip()
                source = str(item.get("resume_quote", "")).strip()
                if not requirement_id or not source:
                    continue
                items.append(
                    {
                        "requirement_id": requirement_id,
                        "source_quote": source,
                        "rewritten": f"{source}；对应岗位要求“{requirement}”可用于简历改写。",
                        "reason": "保守改写：仅使用原文证据，不扩展新事实。",
                    }
                )
        if not items:
            items = [
                {
                    "requirement_id": "req-01",
                    "source_quote": "",
                    "rewritten": "待补充可核实经历后再输出改写。",
                    "reason": "当前未命中可用 JD 依据，先补齐证据。",
                }
            ]
        return json.dumps({"items": items}, ensure_ascii=False)


class MockableDeterministicGateway(DeterministicFallbackGateway):
    """Alias for test readability."""


def build_llm_gateway(config: GatewayConfig | None = None) -> ModelGateway:
    cfg = config or GatewayConfig()
    provider = cfg.provider.strip().lower()

    if provider == "deterministic":
        return DeterministicFallbackGateway()

    # 当前版本保留为“可扩展入口”，先保持离线稳定性
    if provider in {"openai", "deepseek", "vllm"}:
        return DeterministicFallbackGateway()

    raise ValueError(f"unsupported_llm_provider: {provider}")

