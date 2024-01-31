from com.variables import *

# Method to access trade level RM check
def trade_level_rm_check_result(bypass_rm_check, unique_id):

    try:

        # check if bypass rm check value is false and flag to enble rm is true and trade level rm checks are false for unique id
        if (
            bypass_rm_check == "False"
            and variables.flag_enable_trade_level_rm
            and not variables.flag_trade_level_rm_checks[unique_id]
        ):

            return False
        else:

            return True

    except Exception as e:

        return False

# Method to create failure string for trade rm check
def get_failed_checks_string_for_trade_rm_check(unique_id):

    try:

        # Collect keys with False values into a list
        false_keys = [
            key
            for key, value in variables.map_unique_id_to_trade_rm_check_details[
                unique_id
            ].items()
            if not value
        ]

        # Join the list of keys into a comma-separated string
        result = ", ".join(false_keys)

        result += " Failed"

        return result

    except Exception as e:

        return "Details not available"
