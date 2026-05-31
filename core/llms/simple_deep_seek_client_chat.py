"""Non-reasoning DeepSeek client.

Counterpart to ``SimpleDeepSeekClientReasoning``: same DeepSeek API, but
locks ``thinking=False`` + ``model="deepseek-v4-flash"`` (the current
non-reasoning model on DeepSeek's API as of 2026; ``deepseek-chat`` is
deprecated and only kept as a silent alias on the server side) so the
model goes straight to output without spending tokens on
chain-of-thought.

WHY THIS EXISTS
---------------
``SimpleDeepSeekClientReasoning`` (the default ``llm`` for ``task.py
ccx``) uses ``deepseek-v4-pro`` with ``thinking=True``. The reasoning
phase is great when the model genuinely needs to plan a complex
multi-step answer, but it produces a failure mode that broke
``ccx`` doc-mode investigators repeatedly during the 2026-05-21
stock_rec_v4 review:

  * the investigator does 40+ tool rounds reading files,
  * spends most of its remaining token budget *thinking* about how
    to present the findings,
  * runs out of output budget at the JSON-emit step,
  * emits one of these "I'm about to compile the JSON" prose
    sentences with no JSON payload, and
  * doc-mode classifies the result as ``unparseable``/``empty``,
    eventually tripping the synth ``degenerate-run`` gate.

When the LLM's job is mechanical ("extract these specific JSON
fields from what you observed") the thinking phase is pure overhead.
Picking this non-reasoning class for review investigators trades a
small amount of reasoning quality for **much** higher reliability of
the JSON-emit step.

USAGE
-----
Identical surface to ``SimpleDeepSeekClient`` / its Reasoning sibling
— just pass the class name through ``LLMFactory`` or via the
``llm=`` task arg:

    python task.py ccx prompt_file=... agent_mode=doc \
        agent_runner_kind=cc_query_loop llm=SimpleDeepSeekClientChat

``thinking`` is **not** a constructor arg here on purpose: a caller
who wants to toggle reasoning should pick the right class instead of
flipping a bool. If you genuinely need a per-call override, use the
base ``SimpleDeepSeekClient`` and pass ``thinking=...`` yourself.

BUDGET ACCOUNTING
-----------------
``deepseek-chat`` pricing is significantly cheaper than
``deepseek-v4-pro`` reasoning. The cost rate registered in
``stock_rec_v4/runtime/budget.py`` for this client name should match
the current DeepSeek list price for ``deepseek-chat``, NOT inherit
the Reasoning rate (which is ~3× higher).
"""

from typing import Any, Dict, Optional

from core.llms._llm_api_client import LLMApiClient
from core.llms.simple_deep_seek_client import SimpleDeepSeekClient
from ..utils.config_setting import Config


# Forward-declaration shim, mirrors the pattern in
# ``simple_deep_seek_client_reasoning.py``: keeps ``LLMFactory``
# discovery happy when third-party type checkers walk this module
# before the real class is defined below.
class SimpleDeepSeekClientChat(LLMApiClient):
    pass


class SimpleDeepSeekClientChat(SimpleDeepSeekClient):
    def __init__(
        self,
        # ``deepseek-v4-flash`` is the cheap / fast non-reasoning model.
        # ``deepseek-v4-pro`` is also non-reasoning when paired with
        # ``thinking=False`` (the Reasoning sibling above uses the same
        # model but with ``thinking=True``). Callers who want pro-tier
        # quality without reasoning can pass ``model="deepseek-v4-pro"``.
        # ``deepseek-chat`` is deprecated upstream — don't reintroduce it.
        model: str = "deepseek-v4-flash",
        max_tokens: int = 64000,
        temperature: float = 1.0,
        top_p: float = 1,
        presence_penalty: float = 0,
        frequency_penalty: float = 0,
        stop=None,
        # Reasoning is hardcoded OFF for this class. We still accept
        # ``reasoning_effort`` / ``extra_body`` for API parity with
        # the Reasoning sibling, but ``thinking`` is forced to False
        # and ``extra_body`` is rebuilt to match.
        reasoning_effort: Optional[str] = None,
        extra_body: Optional[Dict[str, Any]] = None,
    ):
        config = Config()
        api_key = config.get("deep_seek_api_key")
        # Force ``thinking=False`` regardless of what's in extra_body.
        # If the caller passed their own extra_body, merge ours on top
        # so the thinking-disabled signal wins.
        merged_extra_body: Dict[str, Any] = dict(extra_body or {})
        merged_extra_body["thinking"] = {"type": "disabled"}
        super().__init__(
            api_key=api_key,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            presence_penalty=presence_penalty,
            frequency_penalty=frequency_penalty,
            stop=stop,
            reasoning_effort=reasoning_effort,
            extra_body=merged_extra_body,
            thinking=False,
        )
