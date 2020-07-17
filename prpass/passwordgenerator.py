import abc
import random
import string
import hashlib
import warnings
import functools
import dataclasses

from typing import Tuple

from .hasher import Hasher



CHAR_POOL = (
    string.ascii_lowercase +
    string.ascii_uppercase + 
    string.digits + 
    "~!@#$%^&*()_-=+{}[]|;:'<>?/"
)

# Never ever change this!!!
PUBLIC_BYTES = bytes.fromhex(
    '6a4f329a3fdd67573e356efcf4c66d8b'
    'c410e726413420ffd29889d253719514'
    '58830370945cc29796bd0abc69064285'
    '43244c35e8202f2290753e72670df5f5'
)

_SINGLE_USE_STR = dataclasses.InitVar[str]



class Censored():
    """Prevents accidentally viewing an object in plaintext."""
    def __repr__(self):
        return f'{type(self)}'


class CensoredBytes(Censored, bytes):
    pass




@dataclasses.dataclass
class PasswordGenerator(abc.ABC):
    """Provides the infrastructure to create cryptographically secure
    pseudorandom passwords of arbitrary length. Input parameters are 
    converted to a hash value which is used to seed further pseudo- 
    random hashing operations. 
    
    CPU-bound operations generated by this class are completely 
    decoupled from the object state, meaning they can be pickled,
    sent over the network, submitted to the multiprocessing module,
    or saved to the disk, not that anobody should ever do that...
    
    Important:
    
    This class is insecure if instantiated directly because it cannot
    accept any fields. Therefore, a subclass must be used instead, or
    the PasswordGenerator.new() method, which will automatically create
    a new class or a new object for generating secure passwords. Insecure 
    subclasses configurations are still possible, but they will issue 
    warnings rather than exceptions.
    """
    
    ### Do not add fields here! Use a subclass! ###
    
    
    @classmethod
    def __init_subclass__(cls, **kwargs):
        anno = cls.__annotations__
        for k,v in anno.items():
            if v is not str:
                raise TypeError(
                    f'{cls!r} only accepts {str!r} annotations'
                )
            anno[k] = _SINGLE_USE_STR
        cls = dataclasses.dataclass(cls, frozen=True)
        return cls
    
    
    @classmethod
    def new(cls, *args, **kwargs):
        """Factory function to automatically generate a subclass
        so you don't even have to know how to make a subclass to
        start making passwords! You can even generate multiple
        classes with different parameters! Wowee!
        """
        if args and kwargs:
            raise ValueError(
                'Cannot specify empty fields with filled fields.'
            )
            
            
        random_numer = str(random.getrandbits(12)).zfill(4)
        name = f'_{cls.__name__}_{random_numer}'
        
        # user specified fields only, like a normal subclass with no defaults
        if args:
            new_cls = type(
                name,
                (cls,), 
                {'__annotations__':{
                    k:str for k in args
            }})
            return new_cls
        
        # User specified fields with value names e.g. name='monty'
        else:
            new_cls = type(
                name,
                (cls,), 
                {'__annotations__':{
                    k:str for k in kwargs.keys()
            }})
            return new_cls(**kwargs)
        

    @classmethod
    def get_fields(cls) -> list:
        return list(cls.__annotations__.keys())
        

    @classmethod
    def get_available_algorithms(self):
        return Hasher.get_available_algorithms()

        
    @abc.abstractmethod
    def __init__(self, *args, **kwargs):
        """Abstract method, forcing the caller to use a subclass. 
        Upon subclassing, the dataclass will override __init__ and
        all will be happy
        """
        
        
    def __post_init__(self, *args):
        """Take all the objects supplied to __init__ and use them
        to build a SHA hash, then mega-hash the hash to make the
        user's password seed. If an Executor argument is suppied
        to the constructor, then we will try to submit our work
        to that so we don't block anything.
        """
        params = b''.join(arg.encode() for arg in args)
        
        # basic security nags
        if not params:
            warnings.warn(
                'Insecure configuration: No parameters supplied.'
            )
           
        else:
            if len(params) < 20:
                warnings.warn(
                    'Weak parameters supplied (short inputs).'
                )
                
            if len(set(params)) < 15:
                warnings.warn(
                    'Weak parameters supplied (low variation).'
                )
            
            # # this part requires interpreting the bytes as utf-8
            # param_str = params.decode()  
            # for w in string.whitespace:
                # if w in param_str:
                    # warnings.warn(
                        # 'Whitespace characters in input.'
                    # )
                    # break
            # for w in '\u202f\u2007\u2060\u200b':
                # if w in param_str:
                    # warnings.warn(
                        # 'Invisible unicode characters detected in input.'
                    # )
                    # break
            
            
        salt = hashlib.sha512(params).digest()
        salt = CensoredBytes(salt)

        super().__setattr__('_hasher', Hasher())
        h = self._hasher.build_hash(PUBLIC_BYTES, salt)
        # we are frozen at this point, so we need to call super
        super().__setattr__('_pre_hashed_secret', h)
        
    
    def _reconfigure_initial_hash(self):
        """If set_algorithm is called before the key is 
        set, the backend for constructing the key must be 
        swapped out by first extracting the salt from the 
        initial partial and using it to make a new one.
        """
        salt = self._pre_hashed_secret.keywords  # should be a partial object
        # most KDFs use 'password'. argon2_cffi uses 'secret'
        salt = salt.get('password', False) or salt.get('secret')
        h = self._hasher.build_hash(PUBLIC_BYTES, salt)
        super().__setattr__('_pre_hashed_secret', h)
    
    
    def get_key(self, *, as_partial=True):
        """Compute the hash and verification fingerprint. Lengths of
        each respective value is determined by the hasher class. The
        first half of the hash is interpreted as the "fingerprint",
        sliced from the hash, and discarded after being returned.
        The remaining data is saved as the master key and will be used
        to derive all subsequent hashes.
        """
        if self.has_key():
            return key
        if as_partial:
            return self._pre_hashed_secret
        else:
            return self._pre_hashed_secret()
        
        
    def set_key(self, key) -> bytes:
        """Takes bytes as [fingerprint] + [key], saves the key as an 
        immutable property ``.key'', then returns and discards the 
        fingerprint. The fingerprint is considered PUBLIC information
        and knowing it will not be of any use in determining the key,
        even though they are theoretically linked.
        """
        if not isinstance(key, bytes):
            raise TypeError('Invalid key')
        if len(key) != self._hasher.hash_len:
            raise ValueError('Invalid key length')
        fpl = self._hasher.hash_fingerprint_len
        key_fingerprint, key = key[:fpl], key[fpl:]
        super().__setattr__('key', CensoredBytes(key))
        super().__delattr__('_pre_hashed_secret')
        return key_fingerprint
        
    
    
    def set_algorithm(self, name):
        if self.has_key():
            warnings.warn(
                'Key and passwords should not use different algorithms.'
            )
            
        self._hasher.set_algorithm(name)
        
        if hasattr(self, '_pre_hashed_secret'):
            self._reconfigure_initial_hash()
            
    
    
    def get_hash_name(self):
        return self._hasher.hash_name
    
    
    def has_key(self):
        return bool(getattr(self, 'key', False))
    
    
    def get_password(self, service_name:str, length=25, *, as_partial=False):
        """Construct a partial representing the work factors
        to generate a password. It's pickle-able, so it can
        be passed to an external computation source (like a
        ProcessPoolExecutor), or it can be crunched on the spot,
        the default behavior.
        """

        # make sure we have an adequately sized salt
        service_name = CensoredBytes(
            hashlib.sha512(
                service_name.encode()
            ).digest())
        
        if self.has_key():
            # Set up hash primitives as a partial
            f = self._hasher.build_hash(self.key, service_name, 'fast', length)
            
            # Wrap the hash inside the key decode function
            f = functools.partial(_key_to_password, f, CHAR_POOL)
            
            if as_partial:
                return f
            return f()
        else:
            raise RuntimeError(
                'Key not set (did you forget to call .derive_key()?)'
            )


    def derive_key(self):
        """A convenience function for setting the key up without
        anything fancy. Works in-place, but blocks heavily.
        
        If the caller has a way to handle CPU-bound operations
        properly, it should use .get_key(as_partial=True) to 
        obtain the pre-computed job object, and the .set_key()
        method to write the resultant object back to this object.
        
        Returns the fingerprint of the key
        """
        if self.has_key():
            return
        return self.set_key(self.get_key(as_partial=False))


def _key_to_password(f, p):
    """Interpret a byte string as a series of indices modulo
    the length of a pool string, which is all the characters
    from which the key is allowed to choose.
    
    It's "private" because it's only used with the 
    PasswordGenerator.get_password method, but it can't be local
    otherwise it loses its ability to pickle! So it's global. 
    What a pain.
    """
    return ''.join(p[i%len(p)] for i in f())



