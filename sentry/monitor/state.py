from sentry.openstack.common import timeutils


# Means rpc returns correctly, so service is healthy.
CHECK_OK = 'success'


# Means service offline, so no reply.
CHECK_TIMEOUT = 'timeout'

# Means service is alive, but this rpc is broken, maybe
# incorrect RPC arguments.
CHECK_FAILED = 'failed'


class StateMachine(object):

    def __init__(self):
        self.state = None
        self.start_at = None

    def change_to(self, new_state):
        """Change to next state, if state not changes, return None,
        if state changes, return a tuple (start_at, end_at, durable).
        """
        if self.state is None:
            self.reset(new_state)
            return None

        elif self.state != new_state:
            end_at = timeutils.local_now()
            duration = (end_at - self.start_at).seconds
            changed = {
                'old_state': self.state,
                'new_state': new_state,
                'start_at': self.start_at,
                'end_at': end_at,
                'duration': duration,
            }
            self.reset(new_state)
            return changed

        elif self.state == new_state:
            return None

        else:
            assert "It should not be here."

    def reset(self, state):
        self.state = state
        self.start_at = timeutils.local_now()
