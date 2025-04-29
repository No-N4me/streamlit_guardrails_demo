import streamlit as st
from openai import OpenAI
from validators import validate_user_input, validate_model_output

# Page configuration
st.set_page_config(page_title="Guardrails AI Demo", layout="wide")

# Initialize session state variables
if "messages" not in st.session_state:
    st.session_state.messages = []
if "openai_api_key" not in st.session_state:
    st.session_state.openai_api_key = ""
if "raw_responses" not in st.session_state:
    st.session_state.raw_responses = {}  # To store raw responses for comparison
if "show_comparison" not in st.session_state:
    st.session_state.show_comparison = {}
if "competitor_list" not in st.session_state:
    st.session_state.competitor_list = ["Apple", "Google", "Microsoft", "Amazon", "Facebook"]

st.sidebar.success("✅ Guardrails Demo App Ready!")

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
        ["gpt-4o-mini-2024-07-18", "gpt-4o-2024-11-20", "o4-mini"]
    )
    
    # Temperature slider
    temperature = st.slider("Temperature", min_value=0.0, max_value=1.0, value=0.7, step=0.1)
    
    # Create validators section
    st.header("Guardrails Validators")
    
    # Validators for user input
    st.subheader("Input Validators")
    pii_check = st.checkbox("PII Detection", value=True,
                          help="Detects PII in user input and provides warning")
    jailbreak_check = st.checkbox("Jailbreak Detection", value=True,
                                help="Detects attempts to bypass model safety features")
    
    # Validators for model output
    st.subheader("Output Validators")
    # Competitor Check with customizable list
    competitor_check = st.checkbox("Competitor Check", value=False,
                                 help="Prevents mentioning specific competitor companies in model responses")
    
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
        ### Input Validators
        - **PII Detection**: Identifies personal identifiable information in user input
        - **Jailbreak Detection**: Identifies and blocks attempts to bypass the model's safety features
        
        ### Output Validators
        - **Competitor Check**: Prevents mentioning specific competitor companies in model responses
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
    if pii_check:
        enabled_validators.append("pii_check")
    if jailbreak_check:
        enabled_validators.append("jailbreak_check")
    if competitor_check:
        enabled_validators.append("competitor_check")

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
        # Ensure content is always a string
        content = msg["content"]
        if not isinstance(content, str):
            content = str(content)
        messages.append({"role": role, "content": content})
    
    # Add the current prompt
    # Ensure prompt is a string
    if not isinstance(prompt, str):
        prompt = str(prompt)
    messages.append({"role": "user", "content": prompt})
    
    try:
        # Configure the OpenAI client
        client = OpenAI(api_key=st.session_state.openai_api_key)
        
        # Get a response from the model
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
        )
        raw_response = response.choices[0].message.content
        
        # Store raw response for comparison
        st.session_state.raw_responses[msg_index] = raw_response
        
        # Return raw response if guardrails is disabled
        if not use_guardrails or "competitor_check" not in enabled_validators:
            return raw_response
        
        # Apply output guardrails with improved error handling
        with st.spinner("Applying output validation..."):
            try:
                validated_response = validate_model_output(
                    enabled_validators if use_guardrails else [],
                    raw_response,
                    st.session_state.competitor_list
                )
                return validated_response
            except Exception as e:
                print(f"Output validation error: {str(e)}")
                return f"Note: Output validation encountered an issue. Showing raw response:\n\n{raw_response}"
    
    except Exception as e:
        return f"Error: {str(e)}"

# Function to process new chat message
def process_new_message(prompt):
    original_prompt = prompt
    
    # First validate the user input if guardrails is enabled
    if use_guardrails and any(v in enabled_validators for v in ["pii_check", "jailbreak_check"]):
        with st.spinner("Validating input..."):
            try:
                # Pass the competitor_list parameter
                is_valid, validated_input = validate_user_input(
                    enabled_validators if use_guardrails else [],
                    prompt,
                    st.session_state.competitor_list
                )
                
                if not is_valid:
                    # If input validation fails, show error and don't process the message
                    st.error(validated_input)
                    return
                
                # If input was modified during validation, use the modified version
                if validated_input != prompt:
                    st.warning("Input was modified by Guardrails for safety")
                    prompt = validated_input
            except Exception as e:
                st.error(f"Error during input validation: {str(e)}")
                # Continue with original prompt if validation fails
                prompt = original_prompt
    
    # Add user message to chat history (showing the original prompt to the user)
    st.session_state.messages.append({"role": "user", "content": original_prompt})
    
    # Get the response using the potentially modified prompt
    with st.spinner("Thinking..."):
        response = get_openai_response(prompt, st.session_state.messages[:-1], len(st.session_state.messages))
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})
    
    # Force a rerun to show the updated messages with comparison button
    st.rerun()

# Create a container for the chat
chat_container = st.container()

# Display chat messages
with chat_container:
    for i, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # Add "Show Raw Response" button if this is an assistant message and guardrails was used
            if message["role"] == "assistant" and i in st.session_state.raw_responses and use_guardrails:
                # Initialize this message's comparison state if not already set
                if i not in st.session_state.show_comparison:
                    st.session_state.show_comparison[i] = False
                
                # Button to toggle comparison view
                button_label = "Hide Comparison" if st.session_state.show_comparison[i] else "Compare Raw vs. Validated Response"
                if st.button(button_label, key=f"compare_{i}"):
                    st.session_state.show_comparison[i] = not st.session_state.show_comparison[i]
                    st.rerun()
                
                # Show comparison if enabled for this message
                if st.session_state.show_comparison[i]:
                    st.markdown("### Raw Response (Before Guardrails)")
                    st.markdown(st.session_state.raw_responses[i])
                    st.markdown("### Validated Response (After Guardrails)")
                    st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("What would you like to know?"):
    process_new_message(prompt)

# Add a footer with information
st.markdown("---")
st.markdown("Powered by OpenAI and Guardrails AI | Made with Streamlit")