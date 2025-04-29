import guardrails as gd

from guardrails.hub import (
    GuardrailsPII,
    SecretsPresent,
    DetectJailbreak,
    CompetitorCheck
)

def create_validators(enabled_validators, competitor_list=None):
    """
    Create and return a Guard with the enabled validators.
    
    Args:
        enabled_validators: List of validator names to enable
        competitor_list: Optional list of competitor names for CompetitorCheck
        
    Returns:
        A configured Guard object
    """
    # Create a Guard instance
    guard = gd.Guard()
    

    # Add PII validator
    if "pii_check" in enabled_validators:
        guard.use(
            GuardrailsPII(entities=["PERSON", "EMAIL", "PHONE", "ADDRESS", "SSN", "CREDIT_CARD", "DATE_TIME"], 
                         on_fail="fix")
        )
    
    # Add Secrets validator
    if "secrets_check" in enabled_validators:
        guard.use(
            SecretsPresent, on_fail="fix"  # Using "fix" instead of "exception" to be more user-friendly
        )
    
    # Add Jailbreak detector
    if "jailbreak_check" in enabled_validators:
        guard.use(
            DetectJailbreak, on_fail="fix"
        )
    
    # Add Competitor check
    if "competitor_check" in enabled_validators and competitor_list:
        guard.use(
            CompetitorCheck, competitor_list, on_fail="fix"  # Using "fix" instead of "exception"
        )
    
    return guard

def validate_with_guard(guard, prompt, raw_response):
    """
    Validate a response using the configured Guard.
    
    Args:
        guard: The configured Guard object
        prompt: The user's prompt
        raw_response: The raw response from the LLM
        
    Returns:
        The validated response
    """
    # In this demo application, we're using a basic validation approach
    # In a production environment, you might want to use more sophisticated validation
    try:
        # For some validators like jailbreak, we want to validate the prompt first
        if guard:
            # First check if the prompt contains anything problematic
            guard.validate(prompt)
            
            # Then validate the response
            result = guard.validate(raw_response)
            return result.validated_output
    except Exception as e:
        return f"Guardrails rejected the content with error: {str(e)}\n\nOriginal response: {raw_response}"
    
    return raw_response