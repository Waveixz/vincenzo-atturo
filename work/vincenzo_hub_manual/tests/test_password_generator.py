import unittest

from core.password_generator import DIGIT, LOWER, MAX_LEN, MIN_LEN, SYMBOL, UPPER, derive_password


class PasswordGeneratorTests(unittest.TestCase):
    def test_output_is_deterministic(self):
        first = derive_password("master-test", "servizio", 20, pepper=b"test-pepper")
        second = derive_password("master-test", "servizio", 20, pepper=b"test-pepper")
        self.assertEqual(first, second)

    def test_length_is_clamped(self):
        self.assertEqual(len(derive_password("master", "one", 4, pepper=b"test")), MIN_LEN)
        self.assertEqual(len(derive_password("master", "two", 200, pepper=b"test")), MAX_LEN)

    def test_output_meets_character_policy(self):
        password = derive_password("master-test", "servizio", 20, pepper=b"test-pepper")
        self.assertTrue(any(char in UPPER for char in password))
        self.assertTrue(any(char in LOWER for char in password))
        self.assertTrue(any(char in DIGIT for char in password))
        self.assertTrue(any(char in SYMBOL for char in password))

    def test_required_inputs(self):
        with self.assertRaises(ValueError):
            derive_password("", "servizio", 20, pepper=b"test")
        with self.assertRaises(ValueError):
            derive_password("master", "", 20, pepper=b"test")


if __name__ == "__main__":
    unittest.main()
