import spectrum2
import logging

LOGGER = logging.getLogger(__name__)


class ExampleBackend(spectrum2.Backend):

    def handle_login_request(self, user, legacy_name, password, extra):
        self.handle_connected(user)

        LOGGER.info("User %s connected with legacy name %s", user, legacy_name)

    def handle_logout_request(self, user, legacy_name):
        LOGGER.info("User %s connected with legacy name %s", user, legacy_name)

    def handle_message_send_request(self, user, legacy_name, msg,
                                    xhtml='', mid=0):
        LOGGER.info("User %s sent a message to %s: %s", user, legacy_name, msg)
