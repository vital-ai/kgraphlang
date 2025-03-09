# Runtime Predicates

Predicates may be defined in the parameters an Ensemble Reasoning API call.

This allows a Predicate to be dynamically defined on a per-request basis rather than defined statically in the Ensemble Reasoning implementation code.

Such dynamic predicates are defined by associating a predicate with a certain arity and annotation set with an implementing KGraphService query defined in MetaQL JSON.  This association maps the parameters of the predicate with the parameters of the query.

Other implementations may be added using the KGraphLang, Vital-LLM-Reasoner, Vital-LLM-Reasoner-Server repos.

