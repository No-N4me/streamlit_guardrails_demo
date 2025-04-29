import streamlit as st
from openai import OpenAI
import guardrails as gd
from validators import create_validators, validate_with_guard

# Page configuration
st.set_page_config(page_title="Guardrails AI Demo", layout="wide")

# Initialize session state variables
if "messages" not in st.session_state:
    st.session_state.messages = []
if "openai_api_key" not in st.session_state:
    st.session_state.openai_api_key = ""
if "raw_responses" not in st.session_state:
    st.session_state.raw_responses = {}  # To store raw responses for comparison
if "competitor_list" not in st.session_state:
    st.session_state.competitor_list = ["Apple", "Google", "Microsoft", "Amazon", "Facebook"]

# Main app header
st.title("Guardrails AI Demonstration")

# Sidebar for configuration
with st.sidebar:
    st.header("Configuration")
    
    # API key input
    openai_api_key = st.text_input("OpenAI API Key", type="password", key="input_api_key")
    if openai_api_key:
        st.session_state.openai_api_key = openai_api_key
    
    # Guardrails toggle
    use_guardrails = st.toggle("Enable Guardrails", value=True)
    
    # Model selection
    model = st.selectbox(
        "Select OpenAI Model",
        ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"]
    )
    
    # Temperature slider
    temperature = st.slider("Temperature", min_value=0.0, max_value=1.0, value=0.7, step=0.1)
    
    # Create validators section
    st.header("Guardrails Validators")
    
    # Basic validators
    st.subheader("Basic Validators")
    valid_length = st.checkbox("Valid Length Check", value=True, 
                               help="Ensures responses have an appropriate length (10-500 words)")
    toxicity_check = st.checkbox("Toxicity Check", value=True,
                                help="Prevents harmful or toxic content")
    factual_consistency = st.checkbox("Factual Consistency", value=True,
                                     help="Improves factual accuracy of responses")
    bias_check = st.checkbox("Bias Check", value=True,
                            help="Reduces bias in generated content")
    
    # Advanced validators (from the examples)
    st.subheader("Advanced Validators")
    pii_check = st.checkbox("PII Detection", value=True,
                          help="Detects and removes personally identifiable information")
    secrets_check = st.checkbox("Secrets Check", value=True,
                              help="Prevents exposure of API keys, passwords, etc.")
    jailbreak_check = st.checkbox("Jailbreak Detection", value=True,
                                help="Detects attempts to bypass model safety features")
    
    # Competitor Check with customizable list
    competitor_check = st.checkbox("Competitor Check", value=False,
                                 help="Prevents mentioning specific competitor companies")
    
    if competitor_check:
        competitor_input = st.text_area(
            "Enter competitor names (one per line):",
            value="\n".join(st.session_state.competitor_list)
        )
        st.session_state.competitor_list = [name.strip() for name in competitor_input.split("\n") if name.strip()]
        st.caption(f"Current competitors: {', '.join(st.session_state.competitor_list)}")
    
    # Collapsible section for validator details
    with st.expander("Validator Details"):
        st.markdown("""
        ### Basic Validators
        - **Valid Length**: Ensures the response is between 10-500 words
        - **Toxicity Check**: Filters out harmful, offensive, or inappropriate content
        - **Factual Consistency**: Ensures the response doesn't contain incorrect or misleading information
        - **Bias Check**: Detects and reduces various forms of bias in the response
        
        ### Advanced Validators
        - **PII Detection**: Identifies and removes personal identifiable information like names, emails, addresses, etc.
        - **Secrets Check**: Prevents exposure of API keys, passwords, and other sensitive information
        - **Jailbreak Detection**: Identifies and blocks attempts to bypass the model's safety features
        - **Competitor Check**: Prevents mentioning specific competitor companies in responses
        """)
    
    # About Guardrails section
    with st.expander("About Guardrails AI"):
        st.markdown("""
        **Guardrails AI** is a Python library that helps validate, clean, and improve the outputs from large language models (LLMs).
        
        With Guardrails, you can:
        - Validate LLM outputs against specific criteria
        - Fix problematic outputs automatically
        - Ensure outputs meet your quality standards
        
        This demo lets you see Guardrails in action by applying various validators to responses from OpenAI's models.
        """)
    
    # Put all enabled validators in a list
    enabled_validators = []
    if valid_length:
        enabled_validators.append("valid_length")
    if toxicity_check:
        enabled_validators.append("toxicity_check")
    if factual_consistency:
        enabled_validators.append("factual_consistency")
    if bias_check:
        enabled_validators.append("bias_check")
    if pii_check:
        enabled_validators.append("pii_check")
    if secrets_check:
        enabled_validators.append("secrets_check")
    if jailbreak_check:
        enabled_validators.append("jailbreak_check")
    if competitor_check:
        enabled_validators.append("competitor_check")

# Create the guard with enabled validators
if use_guardrails and enabled_validators:
    guard = create_validators(
        enabled_validators, 
        competitor_list=st.session_state.competitor_list if "competitor_check" in enabled_validators else None
    )
else:
    guard = None

# Display info about current status
if use_guardrails:
    st.info(f"Guardrails is ENABLED with {len(enabled_validators)} active validators")
else:
    st.warning("Guardrails is DISABLED - raw LLM responses will be shown")

# Function to get OpenAI response
def get_openai_response(prompt, history, msg_index):
    if not st.session_state.openai_api_key:
        return "Please add your OpenAI API key in the sidebar."
    
    # Format the conversation history for the API
    messages = []
    for msg in history:
        role = "assistant" if msg["role"] == "assistant" else "user"
        messages.append({"role": role, "content": msg["content"]})
    
    # Add the current prompt
    messages.append({"role": "user", "content": prompt})
    
    try:
        # Configure the OpenAI client
        client = OpenAI(api_key=st.session_state.openai_api_key)
        
        # Check if the prompt itself should be validated first (for jailbreak detection)
        if guard and "jailbreak_check" in enabled_validators:
            try:
                validate_with_guard(guard, prompt, "")
            except Exception as e:
                return f"Guardrails detected a potential issue with your prompt: {str(e)}"
        
        # Get a response without guardrails
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
        )
        raw_response = response.choices[0].message.content
        
        # Store raw response for comparison
        st.session_state.raw_responses[msg_index] = raw_response
        
        # Return raw response if guardrails is disabled
        if not guard:
            return raw_response
        
        # Apply guardrails
        try:
            validated_response = validate_with_guard(guard, prompt, raw_response)
            return validated_response
        except Exception as e:
            return f"Guardrails rejected the response with errors:\n\n{str(e)}\n\nOriginal response: {raw_response}"
    
    except Exception as e:
        return f"Error: {str(e)}"

# Create a container for the chat
chat_container = st.container()

# Display chat messages
with chat_container:
    for i, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # Add "Show Raw Response" button if this is an assistant message and guardrails was used
            if message["role"] == "assistant" and i in st.session_state.raw_responses and use_guardrails:
                if st.button(f"Compare Raw vs. Validated Response", key=f"compare_{i}"):
                    st.markdown("### Raw Response (Before Guardrails)")
                    st.markdown(st.session_state.raw_responses[i])
                    st.markdown("### Validated Response (After Guardrails)")
                    st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("What would you like to know?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Get the current message index
    msg_index = len(st.session_state.messages) - 1
    
    # Display user message
    with chat_container:
        with st.chat_message("user"):
            st.markdown(prompt)
    
        # Display assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = get_openai_response(prompt, st.session_state.messages[:-1], msg_index + 1)
                st.markdown(response)
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})

# Add a footer with information
st.markdown("---")
st.markdown("Powered by OpenAI and Guardrails AI | Made with Streamlit")