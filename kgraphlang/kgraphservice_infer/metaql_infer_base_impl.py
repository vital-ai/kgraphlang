
# base implementation where each predicate is a metaql query
# the results of a query are generated using a generator function
# the results are generated in full before being filtered/combined with the
# surround terms
# this is the naive implementation

# for example:
# person(?p), prop(?p, 'age', ?value), ?value > 30
# this would:
# get every person into a list
# bind ?p to the first one
# eval prop(?p, 'age', ?value) to get a list of ?value
# from the list, bind a value to ?value
# evaluate ?value > 0
# put bound values of ?p, ?value into answer set if evals to true
# backup and repeat for every value of ?value
# backup and repeat for every value of ?p

