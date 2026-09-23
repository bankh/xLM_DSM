#!/bin/bash

python -m graphrag prompt-tune \
    --root "/ragtest/auto_gpt4tp-te3s" \
    --config "/ragtest/auto_gpt4tp-te3s/settings.yaml" \
    --domain "system design" \
    --selection-method random --limit 10 --language English --max-tokens 5120 --chunk-size 1200 --min-examples-required 3 \
    --discover-entity-types --output "/ragtest/auto_gpt4tp-te3s/prompts"