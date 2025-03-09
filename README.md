# kgraphlang


## Documentation Website:
## [https://vital-ai.gitbook.io/kgraphlang](https://vital-ai.gitbook.io/kgraphlang)


## Overview

KGraphLang is a query language designed for LLMs to query Knowledge Graphs.

KGraphLang uses predicates to access knowledge graph nodes and edges, and provides a comprehensive
syntax to compose predicates and generate query results.

KGraphLang is both human friendly and easy for LLMs to generate.

Features include:
* Defining predicates which can be implemented via code or queries to an underlying data source.
* Annotating predicates with extra-logical inputs like @topk(10) to control predicate output
* Aggregations for collections, count, sum, average, max, min
* Math functions for add, subtract, multiply, divide
* Base datatypes: string, number, boolean
* Data types for time, currency, geolocation, units, URIs
* Complex data types for List, Map
* Single and multi-line comments


KGraphLang is used with Ensemble Reasoning to implement the KGraphService Ensemble Member (EM).

Using Ensemble Reasoning a reasoning LLM generates KGraphLang queries and processes results
during the inference.  This avoids the latency of "tool calls" by integrating the knowledge graph directly with the reasoning LLM's model.

---

## Language Features

### General Syntax

A KGraphLang expression always terminates with a period (`.`).

Example:
```kgraph
?x = 10, ?y = 20.
```

### Logical Expressions

Logical expressions can use `AND` (`,`) and `OR` (`;`) to combine multiple statements:

- **AND** expressions:
```kgraph
?x = 10, ?y = 20.
```

- **OR** expressions:
```kgraph
?x = 'Alice'; ?y = 'Bob'.
```

### Variables

Variables start with a question mark (`?`):
```kgraph
?variable_name
```

### Assignment

Use `is` to assign arithmetic expressions to variables:
```kgraph
?total is ?price * ?quantity
```

### Unification

Use `=` for unification:
```kgraph
?status = 'active'
```

### Arithmetic Expressions

Supports arithmetic operations: addition (`+`), subtraction (`-`), multiplication (`*`), and division (`/`):
```kgraph
?result is ?a + ?b * 2
```

### Grouping Expressions

Use parentheses `()` to group expressions and control evaluation order:
```kgraph
(?a + ?b) * 2
```

### Collections (Lists and Maps)

Collections are enclosed in brackets (`[ ]`) and represent lists or maps:

- **List**:
```kgraph
[1, 2, 3, ?var]
```

- **Map**:
```kgraph
['key1' = 'value1', 'key2' = ?var]
```

- **Nested Maps**:
```kgraph
[ 'outer' = [ 'inner_key' = [ 1, 2, 3 ] ] ]
```

### Boolean Values

Booleans are represented as `true` or `false`:
```kgraph
?is_enabled = true
```

### Comparison Operators

Supports comparisons: `>`, `<`, `>=`, `<=`, `==`, `!=`:
```kgraph
?score >= 85
```

### Membership and Subset Operations

- **Membership** (`in`):
```kgraph
?item in ['apple', 'banana']
['key' = 'value'] in ?map
```

- **Subset** (`subset`):
```kgraph
['a', 'b'] subset ['a', 'b', 'c']
['key1' = 'value1'] subset ?larger_map
```

### Negation

Use `not` to negate expressions:
```kgraph
not(?status = 'completed')
```

### Predicates and Annotations

- **Predicates**:
```kgraph
hasRole(?user, 'Admin')
```

Nested predicate calls within arguments are invalid:
  ```kgraph
  child(?x, father(?y))  // INVALID
  ```
  Valid usage:
  ```kgraph
  hasRole(?user, 'Admin')
  ```

- **Annotations** (`@`):
```kgraph
@topk(10) entity_search(?name)
```

### Typed Literals

Explicitly typed literals include:

-- **Date, DateTime, Time, and Duration**:
```kgraph
'2023-02-18'^Date
'2023-02-18T14:30:00'^DateTime
'14:30:00'^Time
'P2Y4M'^Duration
```

- **GeoLocation**:
```kgraph
'40.7128,-74.0060'^GeoLocation
```

- **Currency and Unit**:
```kgraph
'10.00'^Currency(USD)
'100'^Unit('http://qudt.org/vocab/unit/kg')
```

- **URI**:
```kgraph
'http://example.org/resource'^URI
```

### Aggregation

Aggregation functions summarize query results:
```kgraph
sum{ ?amount | ?amount in ?fees }
```

Supported aggregates: `collection`, `set`, `average`, `sum`, `min`, `max`, `count`.

### Strings

Strings use single, double, or triple-double quotes:
```kgraph
'simple string'
"Another string"
"""Multiline
string"""
```

### Comments

- **Single-line** (`//`):
```kgraph
// This is a comment
```

- **Multi-line** (`/* */`):
```kgraph
/* Multi-line
comment */
```

---

## Comprehensive Example

A comprehensive query demonstrating multiple language features:

```kgraph
// define property URIs we want to retrieve
?uri_prop = 'urn:uri_prop'^URI,
?name_prop = 'urn:name_prop'^URI,
?email_prop = 'urn:email_prop'^URI,

?prop_list = [ ?uri_prop, ?name_prop, ?email_prop ],

// get a list of person URIs from the KG
person_uri_list(?PersonList), 

// create a collection of People, with each person
// having a map containing the properties we want
?PersonEmailMapList = collection { 
    ?PersonMapRecord | 
    ?Pid in ?PersonList,
    // get the person info from the KG
    get_person_map(?Pid, ?prop_list, ?PersonMapRecord)
}.
// now the LLM has the desired info from the KG which it can 
// use for the next step in the reasoning process...
```

## Summary

KGraphLang enables expressive and intuitive querying of Knowledge Graphs.

