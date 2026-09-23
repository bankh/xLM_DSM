#!/bin/bash

python -m graphrag prompt-tune \
    --root "/ragtest/PS/auto_deepseek_r1_14b_5k-te3s_r2_r3" \
    --config "/ragtest/PS/auto_deepseek_r1_14b_5k-te3s_r2_r3/settings.yaml" \
    --domain "system design" \
    --selection-method random --limit 10 --language English --max-tokens 5120 --chunk-size 1200 --min-examples-required 3 \
    --discover-entity-types --output "/ragtest/PS/auto_deepseek_r1_14b_5k-te3s_r2_r3/prompts"