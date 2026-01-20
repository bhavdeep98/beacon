#!/bin/bash
# Quick script to open the evaluation report in your default browser

echo "Opening PsyFlo Milestone 1 Evaluation Report..."
open reports/milestone1_evaluation.html 2>/dev/null || \
xdg-open reports/milestone1_evaluation.html 2>/dev/null || \
start reports/milestone1_evaluation.html 2>/dev/null || \
echo "Please open reports/milestone1_evaluation.html in your browser manually"
