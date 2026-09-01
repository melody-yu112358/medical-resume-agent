from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


class ModelGatewayError(RuntimeError):
    pass


class OpenAICompatibleModelGateway:
    """Minimal Chat Completions adapter with no SDK dependency."""

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        timeout_seconds: float = 30,
    ) -> None:
        parsed = urlparse(base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("LLM_BASE_URL must be an absolute http(s) URL")
        if not api_key.strip():
            raise ValueError("LLM_API_KEY cannot be empty")
        if not model.strip():
            raise ValueError("LLM_MODEL cannot be empty")

        normalized = base_url.rstrip("/")
        self.hostname = parsed.hostname or ""
        self.endpoint = (
            normalized
            if normalized.endswith("/chat/completions")
            else f"{normalized}/chat/completions"
        )
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds

    def generate(self, *, task: str, context: dict[str, object]) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": task},
                {
                    "role": "user",
                    "content": json.dumps(context, ensure_ascii=False, separators=(",", ":")),
                },
            ],
            "temperature": 0.2,
            "max_tokens": 4096 if task == "resume_experience_tier_rewrite" else 1200,
            "stream": False,
        }
        if self.hostname == "api.deepseek.com":
            payload["thinking"] = {"type": "disabled"}
        request = Request(
            self.endpoint,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "medical-career-agent/0.1",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                body = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            raise ModelGatewayError(
                f"model API returned HTTP {exc.code}"
            ) from exc
        except (URLError, TimeoutError) as exc:
            raise ModelGatewayError("model API is unreachable") from exc
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ModelGatewayError("model API returned invalid JSON") from exc

        try:
            content = body["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, AttributeError, TypeError) as exc:
            raise ModelGatewayError("model API response has no message content") from exc
        if not content:
            raise ModelGatewayError("model API returned empty content")
        return content
