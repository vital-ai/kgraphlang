import json
import re
import time
from pyergo import pyergo_start_session, pyergo_command, pyergo_query, pyergo_end_session, ERGOVariable
import csv
import io
from kgraphlang.config.reasoner_config import ReasonerConfig
from pyergo import ERGOSymbol

# not needed as we're using the query result object
def split_top_level(s):
    """
    Splits a string (with no outer brackets) on commas that are at the top level.
    Top-level means not inside nested brackets or quoted strings.
    """
    tokens = []
    current = []
    depth = 0         # track nested list depth
    in_quote = False  # track if we're inside a quoted string
    quote_char = None

    for char in s:
        # Handle quoted sections.
        if in_quote:
            current.append(char)
            # End the quoted section if we see the matching quote.
            if char == quote_char:
                in_quote = False
                quote_char = None
            continue

        # Start a quoted section.
        if char in ('"', "'"):
            in_quote = True
            quote_char = char
            current.append(char)
        elif char == '[':
            depth += 1
            current.append(char)
        elif char == ']':
            depth -= 1
            current.append(char)
        # At depth 0, a comma is a separator.
        elif char == ',' and depth == 0:
            tokens.append(''.join(current).strip())
            current = []
        else:
            current.append(char)
    # Append the last token if any.
    if current:
        tokens.append(''.join(current).strip())
    return tokens

# not needed as we're using the query result object
def parse_nested(s):
    """
    Recursively parses a string that represents either a single value or a list.
    A list is recognized by starting with '[' and ending with ']'. For lists,
    the inner content is split into elements using split_top_level, and each
    element is parsed recursively.
    """
    s = s.strip()
    # If it's a list, process the inner content.
    if s.startswith('[') and s.endswith(']'):
        inner = s[1:-1].strip()
        elements = split_top_level(inner)
        return [parse_nested(elem) for elem in elements]
    else:
        # For a plain value, remove outer quotes if present.
        if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
            return s[1:-1]
        return s

def extract_value_list(ergo_list):
    new_list = []
    for e in ergo_list:
        v = extract_value(e)
        new_list.append(v)

    return new_list

def extract_value(ergosymbol_str):

    # should only be these cases

    if isinstance(ergosymbol_str, ERGOSymbol):
        ergosymbol_str = ergosymbol_str.value
        return ergosymbol_str

    if isinstance(ergosymbol_str, ERGOVariable):
        ergosymbol_str = ergosymbol_str.name
        return ergosymbol_str

    if isinstance(ergosymbol_str, list):
        return extract_value_list(ergosymbol_str)

    # shouldn't need other cases

    # ergosymbol_str = str(ergosymbol_str)

    # this case doesn't happen as we're using the object value instead os string parsing
    prefix = "ERGOSymbol(value="

    if ergosymbol_str.startswith(prefix) and ergosymbol_str.endswith(")"):
        s = ergosymbol_str[len(prefix):-1]
        return s

    # this case shouldnt happen as we're using the listy object and not string
    if ergosymbol_str.startswith("[") and ergosymbol_str.endswith("]"):
        parsed = parse_nested(ergosymbol_str)
        if isinstance(parsed, list):
           parsed = extract_value_list(parsed)
        return parsed

    print(f"unhandled ergosymbol_str: {ergosymbol_str}")

    return ergosymbol_str

def main():

    config_file_path = "../reasoner_config.yaml"

    reasoner_config = ReasonerConfig(config_file_path)

    ergo_root = reasoner_config.ERGO_ROOT

    xsb_dir = reasoner_config.XSB_DIR

    pyergo_start_session(xsb_dir, ergo_root)
    pyergo_command("writeln('Hello World!')@\\plg.")

    # pyergo_command("add {'/Users/hadfield/Local/vital-git/kgraphinfer/logic_rules/kgraph_rules.ergo'}.")

    pyergo_command("add {'/Users/hadfield/Local/vital-git/kgraphinfer/test_data/FB15k/output.flr'}.")

    edge_type = "/sports/pro_athlete/teams./sports/sports_team_roster/team"

    query = f"""

    ?_player_set = setof{{ ?player | ?_edge[type -> '{edge_type}', source -> ?player, destination -> ?_team]}}, 
    
    ?player \in ?_player_set,
    
    ?player[label -> ?player_name], 
    
    ?team_set = setof{{ 
        ?team_list | 
        ?_edge[type -> '{edge_type}', source -> ?player, destination -> ?_team], 
        ?_team[label -> ?_team_label], 
        ?team_list = [?_team, ?_team_label] 
    }}.

    """

    query = query.strip()

    # warm up the index
    results_list = pyergo_query(query)

    # count time on warmed up table/index
    start_time = time.perf_counter()

    results_list = pyergo_query(query)

    end_time = time.perf_counter()

    result_list = []

    for item in results_list:
        info = item[0]
        info_dict = {}
        for key, value in info:
            # print(f"{key}: {value}")
            stripped_value = extract_value(value)
            info_dict[key] = stripped_value

        result_list.append(info_dict)

    # print(result_list)

    count = len(result_list)


    c = 0
    for r in result_list:
        c = c + 1
        print(f"Result {c}:")
        json_result = json.dumps(r, indent=4)
        print(json_result)
        print("-" * 100)

    print(f"Result Count: {count}")


    # Calculate the elapsed time (delta)
    delta_time = end_time - start_time
    print(f"Elapsed time: {delta_time:.6f} seconds")

    pyergo_end_session()


if __name__ == "__main__":
    main()


