"""Password policy: one definition, used by the request schema (early 422)
AND the register_user use case (so the bootstrap CLI, which never touches
HTTP, is held to the same rule).

Length-only on purpose. NIST SP 800-63B recommends against composition
rules ("must contain a symbol") and periodic rotation; length is what
actually resists guessing. The upper bound is a sanity limit on request
size and hashing work, not a security feature in itself.
"""

PASSWORD_MIN_LENGTH = 12
PASSWORD_MAX_LENGTH = 128
