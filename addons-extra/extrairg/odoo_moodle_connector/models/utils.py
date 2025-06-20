from . import constants


def get_moodle_credentials(self_env):
    credential = self_env[constants.MOODLE_CREDENTIALS_MODEL].get_default_credentials()
    if constants.RESPONSE_ERROR_KEY not in credential and constants.RESPONSE_ERR_MESSAGE_KEY not in credential:
        return credential
    return None
