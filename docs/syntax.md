# Syntax

Syntax

### Language Features <a href="#language-features" id="language-features"></a>

#### General Syntax <a href="#general-syntax" id="general-syntax"></a>

A KGraphLang expression always terminates with a period (`.`).

Example:

```kgraph
?x = 10, ?y = 20.
```

#### Logical Expressions <a href="#logical-expressions" id="logical-expressions"></a>

Logical expressions can use `AND` (`,`) and `OR` (`;`) to combine multiple statements:

* **AND** expressions:

```kgraph
?x = 10, ?y = 20.
```

* **OR** expressions:

```kgraph
?x = 'Alice'; ?y = 'Bob'.
```

#### Variables <a href="#variables" id="variables"></a>

Variables start with a question mark (`?`):

```kgraph
?variable_name
```

#### Assignment <a href="#assignment" id="assignment"></a>

Use `is` to assign arithmetic expressions to variables:

```kgraph
?total is ?price * ?quantity
```

#### Unification <a href="#unification" id="unification"></a>

Use `=` for unification:

```kgraph
?status = 'active'
```

#### Arithmetic Expressions <a href="#arithmetic-expressions" id="arithmetic-expressions"></a>

Supports arithmetic operations: addition (`+`), subtraction (`-`), multiplication (`*`), and division (`/`):

```kgraph
?result is ?a + ?b * 2
```

#### Grouping Expressions <a href="#grouping-expressions" id="grouping-expressions"></a>

Use parentheses `()` to group expressions and control evaluation order:

```kgraph
(?a + ?b) * 2
```

#### Collections (Lists and Maps) <a href="#collections-lists-and-maps" id="collections-lists-and-maps"></a>

Collections are enclosed in brackets (`[ ]`) and represent lists or maps:

* **List**:

```kgraph
[1, 2, 3, ?var]
```

* **Map**:

```kgraph
['key1' = 'value1', 'key2' = ?var]
```

* **Nested Maps**:

```kgraph
[ 'outer' = [ 'inner_key' = [ 1, 2, 3 ] ] ]
```

#### Boolean Values <a href="#boolean-values" id="boolean-values"></a>

Booleans are represented as `true` or `false`:

```kgraph
?is_enabled = true
```

#### Comparison Operators <a href="#comparison-operators" id="comparison-operators"></a>

Supports comparisons: `>`, `<`, `>=`, `<=`, `==`, `!=`:

```kgraph
?score >= 85
```

#### Membership and Subset Operations <a href="#membership-and-subset-operations" id="membership-and-subset-operations"></a>

* **Membership** (`in`):

```kgraph
?item in ['apple', 'banana']
['key' = 'value'] in ?map
```

* **Subset** (`subset`):

```kgraph
['a', 'b'] subset ['a', 'b', 'c']
['key1' = 'value1'] subset ?larger_map
```

#### Negation <a href="#negation" id="negation"></a>

Use `not` to negate expressions:

```kgraph
not(?status = 'completed')
```

#### Predicates and Annotations <a href="#predicates-and-annotations" id="predicates-and-annotations"></a>

* **Predicates**:

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

* **Annotations** (`@`):

```kgraph
@topk(10) entity_search(?name)
```

#### Typed Literals <a href="#typed-literals" id="typed-literals"></a>

Explicitly typed literals include:

\-- **Date, DateTime, Time, and Duration**:

```kgraph
'2023-02-18'^Date
'2023-02-18T14:30:00'^DateTime
'14:30:00'^Time
'P2Y4M'^Duration
```

* **GeoLocation**:

```kgraph
'40.7128,-74.0060'^GeoLocation
```

* **Currency and Unit**:

```kgraph
'10.00'^Currency(USD)
'100'^Unit('http://qudt.org/vocab/unit/kg')
```

* **URI**:

```kgraph
'http://example.org/resource'^URI
```

#### Aggregation <a href="#aggregation" id="aggregation"></a>

Aggregation functions summarize query results:

```kgraph
sum{ ?amount | ?amount in ?fees }
```

Supported aggregates: `collection`, `set`, `average`, `sum`, `min`, `max`, `count`.

#### Strings <a href="#strings" id="strings"></a>

Strings use single, double, or triple-double quotes:

```kgraph
'simple string'
"Another string"
"""Multiline
string"""
```

#### Comments <a href="#comments" id="comments"></a>

* **Single-line** (`//`):

```kgraph
// This is a comment
```

* **Multi-line** (`/* */`):

```kgraph
/* Multi-line
comment */
```

***

### Comprehensive Example <a href="#comprehensive-example" id="comprehensive-example"></a>

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

\
