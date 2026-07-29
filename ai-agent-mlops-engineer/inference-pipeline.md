# Capability: Inference & Optimization

## Overview
Adapts the model for production constraints and creates robust inference pipelines.

## Operating Instructions
1. **Optimization:** Apply quantization, pruning, or ONNX export if required. **Ask, don't guess:** present the optimization options with trade-offs and a brief recommendation, and let the user decide.
2. **Pipeline:** Build the inference class/API.
3. **V&V:** Verify performance on the test set post-optimization.
4. **Output:** Generate `docs/implementation/Inference_Report.md`.
5. **Review Gate:** Stop. Summarize the pipeline and V&V results, ask the user to review and comment, and wait for explicit approval before declaring the model deployment-ready.
