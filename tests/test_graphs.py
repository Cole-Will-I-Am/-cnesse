"""Unit tests for ecnyss.util.graphs module."""

import unittest
from ecnyss.util.graphs import has_cycle, topological_sort


class TestHasCycle(unittest.TestCase):
    """Tests for the has_cycle function."""

    def test_empty_graph(self):
        """Empty graph has no cycle."""
        self.assertFalse(has_cycle({}))

    def test_single_node_no_edges(self):
        """Single node with no edges has no cycle."""
        self.assertFalse(has_cycle({"A": set()}))

    def test_self_loop(self):
        """A node pointing to itself is a cycle."""
        self.assertTrue(has_cycle({"A": {"A"}}))

    def test_simple_cycle_two_nodes(self):
        """Two nodes pointing to each other form a cycle."""
        graph = {"A": {"B"}, "B": {"A"}}
        self.assertTrue(has_cycle(graph))

    def test_simple_cycle_three_nodes(self):
        """Three nodes in a cycle."""
        graph = {"A": {"B"}, "B": {"C"}, "C": {"A"}}
        self.assertTrue(has_cycle(graph))

    def test_no_cycle_linear_chain(self):
        """Linear chain has no cycle."""
        graph = {"A": {"B"}, "B": {"C"}, "C": set()}
        self.assertFalse(has_cycle(graph))

    def test_no_cycle_dag(self):
        """Valid DAG has no cycle."""
        graph = {"A": {"B", "C"}, "B": {"D"}, "C": {"D"}, "D": set()}
        self.assertFalse(has_cycle(graph))

    def test_disconnected_components_no_cycle(self):
        """Disconnected components without cycles."""
        graph = {"A": {"B"}, "B": set(), "C": {"D"}, "D": set()}
        self.assertFalse(has_cycle(graph))

    def test_disconnected_components_with_cycle(self):
        """Disconnected components where one has a cycle."""
        graph = {"A": {"B"}, "B": {"A"}, "C": {"D"}, "D": set()}
        self.assertTrue(has_cycle(graph))

    def test_cycle_in_disconnected_component(self):
        """Cycle exists in a disconnected component."""
        graph = {"A": set(), "B": {"C"}, "C": {"D"}, "D": {"B"}}
        self.assertTrue(has_cycle(graph))

    def test_node_only_as_successor(self):
        """Node that only appears as successor is handled."""
        graph = {"A": {"B"}}  # B only appears as successor
        self.assertFalse(has_cycle(graph))

    def test_complex_graph_no_cycle(self):
        """Complex DAG without cycles."""
        graph = {
            "A": {"B", "C"},
            "B": {"D", "E"},
            "C": {"E", "F"},
            "D": {"G"},
            "E": {"G"},
            "F": {"G"},
            "G": set()
        }
        self.assertFalse(has_cycle(graph))

    def test_complex_graph_with_cycle(self):
        """Complex graph with a cycle."""
        graph = {
            "A": {"B", "C"},
            "B": {"D"},
            "C": {"D"},
            "D": {"E"},
            "E": {"B"}  # Creates cycle B -> D -> E -> B
        }
        self.assertTrue(has_cycle(graph))


class TestTopologicalSort(unittest.TestCase):
    """Tests for the topological_sort function."""

    def test_empty_graph(self):
        """Empty graph returns empty list."""
        self.assertEqual(topological_sort({}), [])

    def test_single_node(self):
        """Single node returns itself."""
        result = topological_sort({"A": set()})
        self.assertEqual(result, ["A"])

    def test_linear_chain(self):
        """Linear chain returns nodes in order."""
        graph = {"A": {"B"}, "B": {"C"}, "C": set()}
        result = topological_sort(graph)
        self.assertEqual(result, ["A", "B", "C"])

    def test_dag_with_multiple_paths(self):
        """DAG with multiple paths returns valid topological order."""
        graph = {"A": {"B", "C"}, "B": {"D"}, "C": {"D"}, "D": set()}
        result = topological_sort(graph)
        # A must come before B and C, B and C must come before D
        self.assertLess(result.index("A"), result.index("B"))
        self.assertLess(result.index("A"), result.index("C"))
        self.assertLess(result.index("B"), result.index("D"))
        self.assertLess(result.index("C"), result.index("D"))

    def test_disconnected_components(self):
        """Disconnected components are sorted."""
        graph = {"A": {"B"}, "B": set(), "C": {"D"}, "D": set()}
        result = topological_sort(graph)
        # A before B, C before D
        self.assertLess(result.index("A"), result.index("B"))
        self.assertLess(result.index("C"), result.index("D"))

    def test_node_only_as_successor(self):
        """Node only appearing as successor is included."""
        graph = {"A": {"B"}}  # B only appears as successor
        result = topological_sort(graph)
        self.assertEqual(set(result), {"A", "B"})
        self.assertLess(result.index("A"), result.index("B"))

    def test_complex_dag(self):
        """Complex DAG returns valid topological order."""
        graph = {
            "A": {"B", "C"},
            "B": {"D", "E"},
            "C": {"E", "F"},
            "D": {"G"},
            "E": {"G"},
            "F": {"G"},
            "G": set()
        }
        result = topological_sort(graph)
        # Verify all dependencies are respected
        self.assertLess(result.index("A"), result.index("B"))
        self.assertLess(result.index("A"), result.index("C"))
        self.assertLess(result.index("B"), result.index("D"))
        self.assertLess(result.index("B"), result.index("E"))
        self.assertLess(result.index("C"), result.index("E"))
        self.assertLess(result.index("C"), result.index("F"))
        self.assertLess(result.index("D"), result.index("G"))
        self.assertLess(result.index("E"), result.index("G"))
        self.assertLess(result.index("F"), result.index("G"))

    def test_self_loop_raises(self):
        """Self-loop raises ValueError."""
        graph = {"A": {"A"}}
        with self.assertRaises(ValueError):
            topological_sort(graph)

    def test_simple_cycle_raises(self):
        """Simple cycle raises ValueError."""
        graph = {"A": {"B"}, "B": {"A"}}
        with self.assertRaises(ValueError):
            topological_sort(graph)

    def test_complex_cycle_raises(self):
        """Complex cycle raises ValueError."""
        graph = {
            "A": {"B"},
            "B": {"C"},
            "C": {"D"},
            "D": {"B"}  # Creates cycle B -> C -> D -> B
        }
        with self.assertRaises(ValueError):
            topological_sort(graph)

    def test_deterministic_ordering(self):
        """Topological sort produces deterministic ordering."""
        graph = {"A": {"C"}, "B": {"C"}, "C": set()}
        # Run multiple times to ensure determinism
        results = [topological_sort(graph) for _ in range(5)]
        self.assertTrue(all(r == results[0] for r in results))

    def test_all_nodes_in_result(self):
        """All nodes appear in the result."""
        graph = {"A": {"B", "C"}, "B": {"D"}, "C": {"D"}, "D": set()}
        result = topological_sort(graph)
        self.assertEqual(set(result), {"A", "B", "C", "D"})
        self.assertEqual(len(result), 4)


if __name__ == "__main__":
    unittest.main()
