from __future__ import annotations

import json

from medical_career_agent.adapters import openai_compatible_model_gateway as module


class _Response:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    @staticmethod
    def read():
        return b'{"choices":[{"message":{"content":"{}"}}]}'


def test_only_batched_tier_task_gets_larger_output_budget(monkeypatch):
    payloads = []

    def fake_urlopen(request, timeout):
        payloads.append(json.loads(request.data.decode("utf-8")))
        assert timeout == 30
        return _Response()

    monkeypatch.setattr(module, "urlopen", fake_urlopen)
    gateway = module.OpenAICompatibleModelGateway(
        base_url="https://api.example.invalid", api_key="test-key", model="test-model",
    )

    gateway.generate(task="resume_intake_skill_summary", context={})
    gateway.generate(task="resume_experience_tier_rewrite", context={})

    assert [item["max_tokens"] for item in payloads] == [1200, 4096]
