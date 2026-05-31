# Changelog

**English** | [简体中文](./CHANGELOG.zh-CN.md)

## 2024-08-28

- Added portfolio investment recommendations in `llm_dealer`.
- Added recommended portfolio generation in `llm_dealer`.

## 2024-08-27

- Added scheduled stock-selection GitHub Actions in `llm_dealer`.
- Added individual-stock interpretation and prediction features.

## 2024-08-26

- Refactored the futures strategy implementation for maintainability and multi-contract support.
- Refactored AI recommendations to include positive and negative factors.
- Added AI-based futures contract screening.
- Fixed several `llm_dealer` bugs.
- Added `ctp_futures_strategy.py` support for the new `base_futures_strategy.py`.

## 2024-08-20

- Improved futures strategy prompts by including trading history to discourage overly aggressive entries.
- Fixed position opening when the maximum allowed position is `1`.
- Updated AI stock recommendations and expanded evaluation criteria.
- Added `ctp_llm_strategy.py` for CTP-based simulated trading.
- Started improving prompts to reduce knowledge-shadowing effects in LLM analysis.
