from sqlalchemy import Text, TypeDecorator
import bcrypt


class Password(TypeDecorator):
    """Allows storing and retrieving password hashes using PasswordHash."""
    impl = Text

    def __init__(self, rounds=12, **kwds):
        self.rounds = rounds
        super(Password, self).__init__(**kwds)

    def process_bind_param(self, value, dialect):
        """Ensure the value is a PasswordHash and then return its hash."""
        return self._convert(value).hash

    def process_result_value(self, value, dialect):
        """Convert the hash to a PasswordHash, if it's non-NULL."""
        if value is not None:
            return PasswordHash(value)

    def validator(self, password):
        """Provides a validator/converter for @validates usage."""
        return self._convert(password)

    def _convert(self, value):
        """Returns a PasswordHash from the given string.
        PasswordHash instances or None values will return unchanged.
        Strings will be hashed and the resulting PasswordHash returned.
        Any other input will result in a TypeError.
        """
        if isinstance(value, PasswordHash):
            return value
        elif isinstance(value,str):
            return PasswordHash.new(value, self.rounds)
        elif value is not None:
            raise TypeError(
                'Cannot convert {} to a PasswordHash'.format(type(value)))


class PasswordHash(object):

    def __init__(self, hash_):
        #assert len(hash_) == 60, 'bcrypt hash should be 60 chars.'
        if isinstance(hash_, str):
            hash_ = hash_.encode('utf8')
        assert hash_.count(b'$'), 'bcrypt hash should have 3x "$".'
        self.hash = hash_
        self.rounds = int(self.hash.split(b'$')[2])

    def __eq__(self, candidate):
        """Hashes the candidate string and compares it to the stored hash."""
        if isinstance(candidate,str):
                candidate = candidate.encode('utf8')
                cmp_hash = bcrypt.hashpw(candidate, self.hash)
                return cmp_hash == self.hash
        return False

    def __repr__(self):
        """Simple object representation."""
        return '<{}>'.format(type(self).__name__)

    @classmethod
    def new(cls, password, rounds):
        """Creates a PasswordHash from the given password."""
        return cls(bcrypt.hashpw(password.encode('utf8'), bcrypt.gensalt(rounds)))
