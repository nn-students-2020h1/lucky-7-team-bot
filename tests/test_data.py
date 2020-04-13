import unittest
from data import Data


class Test(unittest.TestCase):
    def setUp(self):
        self.data = Data()

    def tearDown(self):
        self.data.data_list = None

    def test_equal(self):
        self.data.fill(5)
        self.assertEqual(self.data.data_list, [0, 2, 4, 6, 8, 10])

    def test_not_equal(self):
        self.data.fill(3)
        self.assertNotEqual(self.data.data_list, [0, 1, 2, 3])

    def test_true(self):
        self.data.fill(4)
        self.assertTrue(self.data.data_list == [0, 2, 4, 6, 8])

    def test_false(self):
        self.data.fill(8)
        self.assertFalse(self.data.total == 76)

    def test_is(self):
        self.data.fill(5)
        self.assertIs(self.data.total, 30)

    def test_is_not(self):
        self.data.fill(5)
        self.assertIsNot(self.data.total, "30")

    def test_in(self):
        self.data.fill(18)
        self.assertIn(34, self.data.data_list)

    def test_not_in(self):
        self.data.fill(18)
        self.assertNotIn(33, self.data.data_list)

    def test_is_none(self):
        self.data.clear()
        self.assertIsNone(self.data.data_list)

    def test_is_not_none(self):
        self.data.fill(5)
        self.assertIsNotNone(self.data.data_list)

    def test_is_instance(self):
        self.data.fill(3)
        self.assertIsInstance(self.data.data_list, list)

    def test_not_is_instance(self):
        self.data.fill(12)
        self.assertNotIsInstance(self.data.data_list, dict)

    def test_warns(self):
        with self.assertWarns(UserWarning):
            self.data.fill("6")

    def test_raises(self):
        with self.assertRaises(TypeError):
            self.data.total = "one hundred"
            self.data.get_sum()

    if __name__ == 'main':
        unittest.main()