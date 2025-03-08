
# Notes on implementation of logic on the grammar

Maps were addd to use for graph objects as a key/value container.

Note: the map functionality could be replaced with a list of 2-item lists, like:
ergo> [[123, ?name]] \subset [[123, 'marc'], [456, 'bob']].
?name = marc

which would avoid the ergoai map implementation.
cases like:
bagof { ?X | ?X in ?Person }
might be ambiguous with ?X being either a list or a map.
but, a case like:
[
    ?uri_prop = ?Pid,
    ?name_prop = ?Name,
    ?email_prop = ?Email
] subset ?PersonMap,

parses as a map so should be ok, and can turn into something like:
[ [ 'urn:uri', ?Pid ], ['urn:name', ?Name], ['urn:email', ?Email] ] \subset
[ [ 'urn:uri', 'urn:123' ], ['urn:email', 'me@you'], ['urn:name', 'marc'] ]

the underlying data would be in frames, so this would involve querying using frames
but when results are processed the data is put into the "list" format such that it'll match
against the "maps" that are used in the kgraph inference expression.

Query results that are in the tuple-list format can be used to create a "parse"
and the un-parse function used to turn it into a map-like string to send to the LLM.
This could mean ergo returns something like:
?R = [ [ 'urn:uri', 'urn:123' ], ['urn:email', 'me@you'], ['urn:name', 'marc'] ]
which would be iterated over 


Note: a predicate like isa(?Thing, ?Class)
might be implemented using:
?Thing:?Class
in ergoai, so functionality of the underlying can be wrapped in functions to simplify
the grammar and LLM integration.
predicates like:
prop_value(?obj_uri, ?prop, ?value)
can be used to access properties of objects/frames like:
?obj[URI -> ?obj_uri, ?prop -> ?value]
isa(?Thing, ?Class) generating an empty set of pairs would make it "false"
so Not (isa(?Thing, ?Class)) would be "true" in that case
so empty set or unbound would be "false"

there are different kinds of "not" so need to be specific about which interpretation we'll be using
i.e. \+, \naf, \neg

so:
not(expression).
might be implemented as 
\naf(expression).

the goal would be something like:

person(?x), not(enemy(?x)), get_email(?x, ?m).

"not" is not a predicate like "person".
it is part of the grammar and takes an expression as parameter.
predicates do not take expressions as parameter, they take an argument list.
in this grammar, predicates do not take predicates as parameters.
