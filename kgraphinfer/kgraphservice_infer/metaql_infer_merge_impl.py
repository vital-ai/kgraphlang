
# this is the implementation which improves over the base implementation by:

# merging predicates, constraints within groups into single metaql query
# use generator functions to generate N results and complete processing those N results
# in the overall query prior to generating N more results

# predicate implementations would need to extend a class that allows
# specifying elements of the metaql query such as traversals
# for instance a predicate:
# traverse(?a, ?b)
# would need to put an "ARC" onto an ARC list that the implementation
# can merge with the other query elements

# something like:
# friend(?P, ?F), prop(?F, 'age', ?V), ?V > 30

# friend() would need to declare it's a traversal over the "hasFriend" edge
# and that ?P and ?F should be "Person" class

# prop() would not define a traversal but would have a binding of a property

# and the filter ?V > 30 would be a constraint on the bound variable

# so these 3 terms should end up in the same metaql query and
# ultimate the same sparql / opencypher query

