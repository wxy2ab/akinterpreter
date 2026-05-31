---
title: LLM Provider Notes
nextjs:
  metadata:
    title: LLM Provider Notes
    description: Historical provider testing notes.
---

**English** | [简体中文](./page.zh-CN.md)

LLM providers behave differently in akinterpreter. Quality, latency, pricing, and regional availability can change over time, so test the providers available to you before choosing a default.

## Historical Notes

- `SimpleClaudeAwsClient` has produced strong code-generation results in project testing.
- `SimpleDeepSeekClient` is inexpensive and easy to configure.
- `SimpleAzureClient` is useful when Azure OpenAI is available in your region.
- `MiniMaxClient`, `GLMClient`, and other providers may be useful for specific workloads.

These notes are not benchmarks and may become outdated as providers update their models.
