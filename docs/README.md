# KGraphLang Overview

KGraphLang

Repo: [https://github.com/vital-ai/kgraphlang](https://github.com/vital-ai/kgraphlang)

KGraphLang is a query language designed for LLMs to query Knowledge Graphs.

KGraphLang uses predicates to access knowledge graph nodes and edges, and provides a comprehensive syntax to compose predicates and generate query results.

KGraphLang is both human friendly and easy for LLMs to generate.

KGraphLang is used with Ensemble Reasoning to implement the KGraphService Ensemble Member (EM).

Features include:

* Defining predicates which can be implemented via code or queries to an underlying data source.
* Annotating predicates with extra-logical inputs like @topk(10) to control predicate output
* Aggregations for collections, count, sum, average, max, min
* Math functions for add, subtract, multiply, divide
* Base datatypes: string, number, boolean
* Data types for time, currency, geolocation, units, URIs
* Complex data types for List, Map
* Single and multi-line comments

