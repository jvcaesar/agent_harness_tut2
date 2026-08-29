import unittest

from demo.main import add


class AddTests(unittest.TestCase):
    def test_positive_sum(self):
        self.assertEqual(add(2, 3), 5)

    def test_zero_sum(self):
        self.assertEqual(add(-1, 1), 0)


if __name__ == "__main__":
    unittest.main()
