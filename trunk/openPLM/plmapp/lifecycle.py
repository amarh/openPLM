try:
    import pygraphviz as pgv
except ImportError:
    print "ImportError : Please install pygraphviz."
    print "It's used to generate graphes from lifecycle"

_lifecycles_list = [
    ("draft", "official", "deprecated"),
    ("draft", "official"),
]



class LifecycleList(list):
    u"""
    Object which represents a lifecycle as a list of string.

    This class inherits from list, so you can use all list methods.
    For example::

        >>> cycle = LifecycleList("MyCycle")
        >>> cycle.extend(["a", "b", "c"])
        >>> cycle[0]
        'a'

    .. attribute:: name

        name of the lifecycle

    """
    def __init__(self, name, *args):
        super(LifecycleList, self).__init__(self)
        self.name = name
        self.extend(args)

    def next_state(self, state):
        u"""
        Returns the next state of *state*

        Raises :exc:`ValueError` if *state* is not in the list and :exc:`IndexError`
        if *state* is the last state.
        
        Example::

            >>> cycle = LifecycleList("MyCycle", "a", "b", "c", "d")
            >>> cycle.next_state("b")
            'c'
            >>> cycle.next_state("d")
            Traceback (most recent call last):
                ...
            IndexError: list index out of range

            >>> cycle.next_state("z")
            Traceback (most recent call last):
                ...
            ValueError: list.index(x): x not in list

        """
        index = self.index(state)
        return self[index + 1]
    
    def previous_state(self, state):
        u"""
        Returns the previous state of *state*

        Raises :exc:`ValueError` if *state* is not in the list and :exc:`IndexError`
        if *state* is the first state.

        Example::

            >>> cycle = LifecycleList("MyCycle", "a", "b", "c", "d")
            >>> cycle.previous_state("b")
            'a'
            >>> cycle.previous_state("a")
            Traceback (most recent call last):
                ...
            IndexError

            >>> cycle.previous_state("z")
            Traceback (most recent call last):
                ...
            ValueError: list.index(x): x not in list


        """
        index = self.index(state)
        if index - 1 < 0:
            raise IndexError()
        return self[index - 1]

    def draw_graph(self, current_state, output_path,
                   normal_color="#7a7af8", current_color="#0808fa"):
        u"""
        Draws a graph (with pygraphviz) of the lifecycle. 

        :param current_state: current state to highlight, may be empty
        :type cuurent_state: str
        :param output_path: pathname of the generated png
        :type output_path: str
        :param normal_color: fill color of normal states
        :type normal_color: an html color (like ``cyan`` or ``#110011``)
        :param current_color: fill color of current state
        :type current_color: an html color (like ``cyan`` or ``#110011``)

        """
        graph = pgv.AGraph(directed=True)
        graph.graph_attr["rankdir"] = "LR"
        graph.graph_attr["bgcolor"] = "#00000000" # transparent
        graph.node_attr["style"] = "filled"
        graph.node_attr["fillcolor"] = normal_color
        graph.add_edges_from(zip(self, self[1:]))
        if current_state:
            node = graph.get_node(current_state)
            node.attr["fillcolor"] = current_color
        graph.draw(path=output_path, format="png", prog="dot")


lifecycles = dict()
for cycles in _lifecycles_list:
    name = "->".join(cycles) 
    lifecycles[name] = LifecycleList(name, *cycles)

if __name__ == "__main__":
    import doctest
    doctest.testmod()
