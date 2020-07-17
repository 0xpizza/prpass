import hashlib
import functools

# find and configure available KDF algorithms
# if found, add hash function and arguments as a tuple to global list
# algorithms are added *in order* from most to least preferrable.
# hashes have two modes determined by their "work factor" parameter:
# slow is used for initial secret derivation, and fast is for 
# subsequent pseudo-random password generation.
AVAILABLE_ALGORITHMS = dict()
try:
    import argon2
    AVAILABLE_ALGORITHMS.update(
        argon2 = (argon2.low_level.hash_secret_raw,
                    dict(
                        memory_cost = 1024 * 2000, #KiB
                        parallelism=8, 
                        type=argon2.Type.ID),
                    dict(
                        fast = {'time_cost': 2},
                        slow = {'time_cost': 4},
                    )))
except ImportError:
    pass

try:
    AVAILABLE_ALGORITHMS.update(
        scrypt = (hashlib.scrypt,
                    dict(
                        r=8, 
                        p=1,
                        maxmem = 0x7fffffff),
                    dict(
                        fast = {'n': 2**16},
                        slow = {'n': 2**20},
                    )))
except NameError:
    pass

# TODO: add bcrypt
# try:
    # import bcrypt
    # AVAILABLE_ALGORITHMS.update(
        # bcrypt = (bcrypt.hash,
                    # dict(),
                    # dict(),
                    # ))
                    
# except ImportError:
    # pass

try:
    AVAILABLE_ALGORITHMS.update(
        pbkdf2 = (hashlib.pbkdf2_hmac,
                    dict(
                        #iterations=,
                        #dklen=
                    ),
                    dict(
                        fast = {'iterations': 400000},
                        slow = {'iterations': 700000},
                    )))
                    
except NameError:
    pass



if not AVAILABLE_ALGORITHMS.keys():
    raise RuntimeError(
        'No suitable hash algorithms found!'
    )


# the first 16 bytes should not be used for anything other than
# verification of the inputs. That means discard them.
HASH_FINGERPRINT_LEN = 16
HASH_LEN = 64 + HASH_FINGERPRINT_LEN



class Hasher():
    """Interface class for working with different 
    hash algorithm backends. Algorithms supported:
        - Scrypt
        - Argon2 (id)
        - PBKDF2
    """
    
    @staticmethod
    def get_available_algorithms():
        return list(AVAILABLE_ALGORITHMS.keys())
    

    def __init__(self, algorithm=None):
        if algorithm is None:
            algorithm = Hasher.get_available_algorithms()[0]  # get best
        self.set_algorithm(algorithm)
    
    def set_algorithm(self, algorithm):
        if not algorithm in Hasher.get_available_algorithms():
            raise ValueError(
                f'Algorithm not available: {algorithm}'
            )
        a = AVAILABLE_ALGORITHMS[algorithm]
        self._hash_name = algorithm
        self._hash_function = a[0]
        self._hash_params = a[1]
    
    
    def hash(self, *args, **kwargs):
        """Convinience function to do a hash immediately."""
        return self.get_hash(*args, **kwargs)()
    
    
    def build_hash(self, secret, salt, work_factor='slow', dklen=HASH_LEN):
        """Build a generic hash job as a partial which can be
        evaluated at the caller's discretion.
        """
        
        if (   self._hash_function is hashlib.scrypt 
            or self._hash_function is hashlib.pbkdf2_hmac):
            self._hash_params['salt'] = salt
            self._hash_params['password'] = secret
            self._hash_params['dklen'] = dklen
            
        if self._hash_function is argon2.low_level.hash_secret_raw:
            self._hash_params['salt'] = salt
            self._hash_params['secret'] = secret
            self._hash_params['hash_len'] = dklen
            self._hash_params.update(
                AVAILABLE_ALGORITHMS['argon2'][2][work_factor]
            )
                
        if self._hash_function is hashlib.scrypt:
            self._hash_params.update(
                AVAILABLE_ALGORITHMS['scrypt'][2][work_factor]
            )
        
        if self._hash_function is hashlib.pbkdf2_hmac:
            self._hash_params['hash_name'] = 'SHA256'
            self._hash_params.update(
                AVAILABLE_ALGORITHMS['pbkdf2'][2][work_factor]
            )
        
        return functools.partial(self._hash_function, **self._hash_params)
        
        
    @property
    def hash_name(self):
        return self._hash_name
    
    @property
    def hash_len(self):
        return HASH_LEN
        
    @property
    def hash_fingerprint_len(self):
        return HASH_FINGERPRINT_LEN