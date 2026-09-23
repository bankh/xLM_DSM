#!/bin/bash

python -m graphrag prompt-tune \
    --root "/ragtest/CS/auto_deepseek_r1_14b_5k_r1_r2-te3s" \
    --config "/ragtest/CS/auto_deepseek_r1_14b_5k_r1_r2-te3s/settings.yaml" \
    --domain "system design" \
    --selection-method random --limit 10 --language English --max-tokens 5120 --chunk-size 1200 --min-examples-required 3 \
    --discover-entity-types --output "/ragtest/CS/auto_deepseek_r1_14b_5k_r1_r2-te3s/prompts"