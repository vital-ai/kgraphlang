from abc import ABC, abstractmethod
from kgraphlang.kgraph_infer import UNBOUND, BindingStack

class KGraphPredicate(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def eval_impl(self, input_dict: dict) -> list:
        """
        Given a dictionary mapping parameter indices to either a bound value or UNBOUND,
        return a list of dictionaries mapping parameter indexes to concrete candidate values.
        """
        pass

    def is_variable(self, arg):
        return isinstance(arg, str) and arg.startswith("?")

    def evaluate(self, args, binding: BindingStack):
        # Build an input dictionary: index -> value (or UNBOUND)
        input_dict = {}
        for i, arg in enumerate(args):
            if self.is_variable(arg):
                if arg in binding:
                    input_dict[i] = binding.get(arg)
                else:
                    input_dict[i] = UNBOUND
            else:
                input_dict[i] = arg
        # Delegate to the implementing function.
        outputs = self.eval_impl(input_dict)
        new_bindings = []
        for output in outputs:
            new_binding = binding.copy()
            conflict = False
            for i, arg in enumerate(args):
                if self.is_variable(arg):
                    # If already bound, ensure consistency.
                    if arg in new_binding:
                        if new_binding.get(arg) != output.get(i):
                            conflict = True
                            break
                    else:
                        new_binding.bind(arg, output.get(i))
            if not conflict:
                new_bindings.append(new_binding)
        return new_bindings
