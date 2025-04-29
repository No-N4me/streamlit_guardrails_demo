import guardrails as gd
from guardrails.validators import PassResult, FailResult
from guardrails.hub import (
    GuardrailsPII,
    DetectJailbreak,
    CompetitorCheck
)

def check_for_pii(text):
    """Simple wrapper to check for PII in text."""
    try:
        # Create a guard with the PII validator
        guard = GuardrailsPII(
                    entities=["PERSON", "EMAIL", "PHONE", "ADDRESS", "SSN", "CREDIT_CARD", "DATE_TIME"],
                    on_fail="fix"
                )
        # Run the validation
        try:
            result = guard.validate(value=text, metadata={})
            print(f"PII validation result: {result}")
            # Ensure we return a string, not an object
            if isinstance(result, FailResult):
                return True, result.fix_value
            elif isinstance(result, PassResult):
                return True, text
            else:
                return True, str(result)  # Last resort - convert whatever we got to string
        except Exception as e:
            print(f"PII validation error: {str(e)}")
            return False, f"PII detected in input: {str(e)}"
    
    except Exception as e:
        print(f"Error setting up PII validation: {str(e)}")
        return True, text  # Fail open by default

def check_for_jailbreak(text):
    """Simple wrapper to check for jailbreak attempts in text."""
    try:
        # Create an instance of DetectJailbreak
        validator = DetectJailbreak()
        # Validate the text with required metadata parameter
        result = validator.validate(value=text, metadata={})
        
        print(f"Jailbreak validation result: {result}")

        if isinstance(result, FailResult):
            print(f"Jailbreak attempt detected: {result}")
            return False, result.fix_value
        elif isinstance(result, PassResult):
            print("No jailbreak attempt detected.")
            return True, text
        else:
            return True, str(result)  # Last resort - convert to string
    except Exception as e:
        print(f"Jailbreak attempt detected: {str(e)}")
        return False, f"Potential jailbreak attempt detected: {str(e)}"

def check_for_competitors(text, competitor_list):
    """Simple wrapper to check for competitor mentions in text."""
    if not competitor_list:
        return True, text
    
    try:
        # Create an instance of CompetitorCheck
        validator = CompetitorCheck(on_fail="fix")
        # Validate the text with required metadata parameter
        result = validator.validate(value=text, metadata={}, validator_params=competitor_list)

        print(f"Competitor validation result: {result}")
        
        if isinstance(result, FailResult):
            return False, result.fix_value
        elif isinstance(result, PassResult):
            return True, text
        else:
            return True, str(result)  # Last resort - convert to string
    except Exception as e:
        print(f"Competitor mentions found: {str(e)}")
        
        # Simple sanitization as fallback
        sanitized = text
        for competitor in competitor_list:
            sanitized = sanitized.replace(competitor, "[COMPETITOR]")
        
        return True, sanitized

def validate_user_input(enabled_validators, user_input, competitor_list=None):
    """
    Validate user input using enabled validators.
    
    Args:
        enabled_validators: List of enabled validator names
        user_input: Text to validate
        competitor_list: List of competitor names (not used for input)
        
    Returns:
        Tuple of (is_valid, message_or_validated_input)
    """
    if not enabled_validators:
        return True, user_input
    
    current_text = user_input
    modified = False
    
    # Check for jailbreak attempts
    if "jailbreak_check" in enabled_validators:
        is_valid, result = check_for_jailbreak(current_text)
        if not is_valid:
            return False, "Jailbreak attempt detected, prompt rejected."
        if result != current_text:
            current_text = result
            modified = True
    
    # Check for PII
    if "pii_check" in enabled_validators:
        is_valid, result = check_for_pii(current_text)
        if not is_valid:
            return False, result
        if result != current_text:
            current_text = result
            modified = True
    
    # Return the potentially modified input
    return True, current_text

def validate_model_output(enabled_validators, model_output, competitor_list=None):
    """
    Validate model output using enabled validators.
    
    Args:
        enabled_validators: List of enabled validator names
        model_output: Text to validate
        competitor_list: List of competitor names
        
    Returns:
        Validated output or original if no changes
    """
    if not enabled_validators or "competitor_check" not in enabled_validators:
        return model_output
    
    # Check for competitor mentions
    is_valid, result = check_for_competitors(model_output, competitor_list)
    
    # If modified, add a note
    if result != model_output:
        return f"Note: Output was modified to remove competitor mentions.\n\n{result}"
    
    return model_output