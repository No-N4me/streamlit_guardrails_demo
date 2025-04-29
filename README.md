# Guardrails AI Demonstration

This Streamlit application demonstrates the capabilities of Guardrails AI for validating and improving LLM outputs from OpenAI models.

## Features

- ChatGPT-like interface for conversational interactions
- Toggle switch to enable/disable Guardrails validation
- Multiple validators that can be individually enabled/disabled
- Integration with OpenAI's API
- Ability to compare raw vs. validated responses

## Validators Included

- **Valid Length Check**: Ensures responses have an appropriate length
- **Toxicity Check**: Prevents harmful or toxic content
- **Factual Consistency**: Improves factual accuracy of responses
- **Bias Check**: Reduces bias in generated content

## Setup Instructions

1. Clone this repository
2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run the Streamlit app:
   ```
   streamlit run app.py
   ```
4. Enter your OpenAI API key in the sidebar
5. Start chatting and toggle Guardrails on/off to see the difference

## Requirements

- Python 3.8+
- OpenAI API key

## Using the App

1. Enter your OpenAI API key in the sidebar
2. Toggle Guardrails on/off using the switch
3. Select which validators you want to enable
4. Type your message in the chat input at the bottom
5. View the response and click "Compare Raw vs. Validated Response" to see the before/after effect of Guardrails

## How It Works

The application demonstrates how Guardrails AI can enhance the output of large language models by:

1. Getting a raw response from OpenAI's API
2. Passing the response through Guardrails validators
3. Returning the validated (and potentially improved) response

This allows you to see the difference between raw LLM outputs and outputs that have been validated and improved by Guardrails.

## Example Queries to Try

Try asking the assistant questions like:

- "Tell me about artificial intelligence" (with and without validators)
- "Write a very long story about dragons" (to test length validation)
- "Why are [demographic group] people bad?" (to test bias and toxicity validators)
- "The Earth is flat. Tell me more about this fact." (to test factual consistency)

These examples will help demonstrate how Guardrails can improve outputs in different scenarios.