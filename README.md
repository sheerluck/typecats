# typecats
Structure unstructured data for the purpose of static type checking

In many web services it is common to consume or generate JSON or some
JSON-like representation of data. JSON translates quite nicely to core
Python objects such as dicts and lists. However, if your data is
structured, it is nice to be able to work with it in a structured
manner, i.e. with Python objects. Python objects give you better code
readability, and in more recent versions of Python they are also
capable of being statically type-checked with a tool like `mypy`.

`attrs` is an excellent library for defining boilerplate-free Python
classes that are easy to work with and that make static type-checking
with `mypy` a breeze. You define your attributes and their types with
a very clean syntax, `attrs` gives you constructors and dunder
methods, and `mypy` brings the static type-checking.

Throwing `cattrs` into the mix, you can have pleasant and simple
conversions to and from unstructured data with extremely low
boilerplate as well.

`typecats`, and its core decorator `Cat`, is a thin opionated layer on
top of these two runtime libraries (`attrs` and `cattrs`) and the
develop-time `mypy`. It defines an `attrs` class with a few additional
features. The 3 core features are:

### Features

1. Static class `struc` function and object `unstruc` method added to
   every class type defined as a Cat.

   ```
   @Cat
   class TestCat:
	   name: str
	   age: int

   TestCat.struc(dict(name='Tom', age=9)) == TestCat(name='Tom', age=9)

   TestCat.struc(dict(name='Tom', age=9)).unstruc() == dict(name='Tom', age=9)
   ```

   Rationale:

   Make your code easier to read, create a common pattern for
   structuring and unstructuring pure data objects, and require fewer
   imports - just import your defined type and go!

2. Non-empty validators defined for all attributes with no default
   provided.

   ```
   @Cat
   class TestCat:
	   name: str
	   age: int
	   neutered: bool = True
	   owner: Optional[Owner] = None

   works = TestCat.struc(dict(name='Tom', age=0))
   works.neutered == True

   try:
	   TestCat.struc(dict(name='', age=0))
   except ValueError as ve:
	   print(ve)
	   # Attribute "name" on class <class 'TestCat'> with type <class 'str'> cannot have empty value ''!
   ```

   Rationale:

   For many types of data, a default value such as an empty string,
   empty list/set, or missing complex type is perfectly valid, and
   `typecats` takes the approach that such attributes should have a
   defined default value in order to simplify the use of those
   objects. This has been found to be particularly useful in the
   context of structuring data from APIs, where the API contract may
   not require all keys to be provided for a given type, and where new
   attributes/keys may be defined later on that old clients would not
   know about (backwards compatibility).

   On the other hand, there are some facets of the data that are
   absolutely required. A common example would be a database ID -
   without a defined ID, the object/data is meaningless. `typecats`
   allows you to enforce the most basic level of compliance by not
   defining defaults, which forces clients to provide not simply a
   value of the proper type, but a non-empty value of that type - the
   empty string would never be a valid database ID.

3. Objects may subclass `dict` in order to transparently retain
   untyped keys for a roundtrip structure-unstructure. These are
   called `Wildcats`, since they allow a significant amount of extra
   functionality at the cost of not fully enforcing type-checking.

   ```
   @Cat
   class TestWildcat(dict):
	   name: str
	   age: int

   cat_from_db = dict(name='Tom', age=8, gps_tracker=True)
   wc = TestWildcat.struc(cat_from_db)
   assert wc.name == Tom
   assert wc.age == 8
   assert wc['gps_tracker'] == True
   assert wc.unstruc() == cat_from_db  # `gps_tracker` survived the roundtrip
   ```

   Rationale:

   In other static type-checking systems such as Flow for JavaScript,
   you may define a type as being a simple overlay on top of an object
   which does not prevent that object from containing other data. A
   `Cat` is an `attrs` class with a defined set of attributes that
   will be structured from raw data, and as of `cattrs` 1.0.0rc0,
   unexpected keys are silently dropped in order to prevent users from
   needing to sanitize their data before structuring. This means that
   a structured object is not suitable for being passed between
   different parts of a program if there may be other parts to the
   data that the structuring class does not know about. Since many
   structuring/unstructuring trips can be prohibitively expensive, and
   additionally it is arguably (e.g., the design philosophy behind
   Clojure's Maps, or simply duck/structural typing in general) better
   software design to allow code to operate on a limited subset of
   attributes without preventing objects with a superset of their
   functionality to be used, `typecats` provides the `Wildcat`
   functionality to mimic these more expressive and flexible type/data
   systems.

   Note that, as with the rest of `typecats`, this is a local optimum
   designed for specific though arguably common usecases. You don't
   need to use the Wildcat functionality to take advantage of features
   1 and 2, and since it is presumably quite rare to explicity
   subclass `dict` for normal Python classes, it seems unlikely that
   this implementation choice to require inheritance would prevent
   most practical use cases of `Cat` even if the functionality of
   preserving unknown data was specifically not desirable for a given
   application.

   A further design note on Wildcats: A non-inheriting implementation
   was considered and rejected (so far) for two reasons: first, that
   this would require major additional work in order to support
   `pylint` and `mypy` understanding that dict-like access was legal
   for these objects; and second, that *not* inheriting `dict` but
   overriding `__getitem__` and `__setitem__` would be even more
   likely to conflict with existing class hierarchies, since any
   object that already inherited from `dict` would appear to 'work' as
   a Wildcat but its underlying `dict` would be overlaid and
   inaccessible as a Wildcat.


### Notes on intent, compatibility, and dependencies

`typecats` and `Cat` are explictly intended to solve a *few* specific
but common uses, and though they do not intentionally override or
replace `attrs` or `cattrs` features, any complex use of those
underlying features may or may not be fully operational. If you want
to write complex validator or constructor/builder logic of your own,
this library may not be for you.

That said, it is common in our experience to register a number of
specific structure and unstructure hooks with `cattrs` to make certain
specific scenarios work ideally with your data, and `typecats`
provides convenient wrappers to allow adding your hooks to its
internal `cattrs` `Converter` instance. By defining its own converter
instance, `typecats` does not interfere in any way with an existing
application's usage of `attrs` or `cattrs`, and may be used in
addition to, rather than as a replacement for, those libraries.

`typecats` uses newer-style static typing within its own codebase, and
is therefore currently only compatible with Python 3.6 and up.

As core parts of the implementation, both `attrs` and `cattrs` are
runtime dependencies.