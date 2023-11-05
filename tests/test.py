import unittest
from unittest.mock import MagicMock
from graphWriter import GraphWriter  # Replace 'project' with the name of your project file.
from graphWriter.graphWriter import PlotHandler

# Mock the SummaryWriter
SummaryWriter = MagicMock()

class TestPlotHandler(unittest.TestCase):
    
    def test_init(self):
        tag = 'TestTag'
        data = [1, 2, 3, 4, 5]
        plot_handler = PlotHandler(tag, data)
        self.assertEqual(plot_handler.tag, tag)
        self.assertEqual(plot_handler.data, data)

class TestGraphWriter(unittest.TestCase):
    
    def test_add_scalar(self):
        writer = SummaryWriter()
        graph_writer = GraphWriter(writer)
        tag = 'Test/Scalar'
        scalar_value = 10
        graph_writer.add_scalar(tag, scalar_value)
        # Assuming that add_scalar is supposed to update scalar_data
        self.assertEqual(graph_writer.scalar_data[tag][-1], scalar_value)

if __name__ == '__main__':
    unittest.main()
