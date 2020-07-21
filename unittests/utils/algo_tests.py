#               _   _                                  _            _ _ _           _
#    __ _ _ __ | |_(_)___ _ __   __ _ _ __ ___      __| | _____   _(_) | |__   ___ | |_
#   / _` | '_ \| __| / __| '_ \ / _` | '_ ` _ \    / _` |/ _ \ \ / / | | '_ \ / _ \| __|
#  | (_| | | | | |_| \__ \ |_) | (_| | | | | | |  | (_| |  __/\ V /| | | |_) | (_) | |_
#   \__,_|_| |_|\__|_|___/ .__/ \__,_|_| |_| |_|___\__,_|\___| \_/ |_|_|_.__/ \___/ \__|
#                        |_|                  |_____|
#
# Remove excess mentions in telegram groups
# Copyright (C) 2020 Nikita Serba. All rights reserved
# https://github.com/sandsbit/antispam_devilbot
#
# antispam_devilbot is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License.
#
# antispam_devilbot is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with antispam_devilbot. If not, see <https://www.gnu.org/licenses/>.

from __future__ import annotations

import unittest
from math import inf

from typing import Union

from antispam.utils.algo import binary_search, NotFound


class ComparableInt:
    """
    Just stores int value. Used in binary_search tests to test search in
    lists of objects.
    """

    value: int

    def __init__(self, value: int):
        self.value = value

    def __lt__(self, other: Union[ComparableInt, int, float]) -> bool:
        if isinstance(other, ComparableInt):
            return other.value > self.value
        else:
            return other > self.value

    def __gt__(self, other: Union[ComparableInt, int, float]) -> bool:
        if isinstance(other, ComparableInt):
            return other.value < self.value
        else:
            return other < self.value

    def __eq__(self, other: Union[ComparableInt, int, float]) -> bool:
        if isinstance(other, ComparableInt):
            return other.value == self.value
        else:
            return other == self.value


class TestBinarySearch(unittest.TestCase):
    """Test binary_search method from skarma.utils.algo"""

    def _assertThrowNotFound(self, *args, **kwargs):
        """Check that binary_search raise NotFound"""

        with self.assertRaises(NotFound):
            binary_search(*args, **kwargs)

    def _assertEveryElementCanBeFound(self, test_list: list):
        """Checks that binary_search return index of element in test_list"""

        for i in range(len(test_list)):
            with self.subTest('Every element can be found', i=i):
                self.assertEqual(
                    binary_search(test_list[i], test_list),
                    i
                )

    def test_search_int(self):
        """Test binary search between integers"""

        test_list = [0, 2, 5, 7, 9, 13, 345, 1937]

        self._assertEveryElementCanBeFound(test_list)

    def test_search_mixed(self):
        """Test search for int or float in list of ints and floats"""

        test_list = [-inf, -134, -34.5, -5, 0, 23, 23.00001, 234, inf]

        self._assertEveryElementCanBeFound(test_list)

    def test_search_str(self):
        """Test search in list of strings"""

        test_list = sorted(['master', 'PC', 'symbol', 'silicon', 'ssd', 'slave', 'sin', '#$@!',
                            ' need healing', '#^37', '23', '2345', '3457', '9'])

        self._assertEveryElementCanBeFound(test_list)

    def test_not_found(self):
        """Test search for element that is not in list"""

        test_array = [1, 2, 4, 78]
        with self.subTest(test_array=test_array):
            self._assertThrowNotFound(3, test_array)
            self._assertThrowNotFound(0.5, test_array)

        test_array = [-inf, 1.004, 2, 4.000000000005, 78]
        with self.subTest(test_array=test_array):
            self._assertThrowNotFound(1, test_array)
            self._assertThrowNotFound(3, test_array)
            self._assertThrowNotFound(4, test_array)
            self._assertThrowNotFound(inf, test_array)

        test_array = sorted(['12', '1273', '&362', ' ok', 'None'])
        with self.subTest(test_array=test_array):
            self._assertThrowNotFound('ok', test_array)
            self._assertThrowNotFound('&', test_array)

        test_array = []
        with self.subTest(test_array=test_array):
            self._assertThrowNotFound(0, test_array)
            self._assertThrowNotFound(None, test_array)
            self._assertThrowNotFound('', test_array)

    def test_search_objects(self):
        """Test that search works with searching objects"""

        test_int_array = [-83, 27, 69, 76, 83, 245]
        test_array = [ComparableInt(x) for x in test_int_array]

        self._assertEveryElementCanBeFound(test_array)

        for i in range(len(test_int_array)):
            with self.subTest('You can found ComparableInt by int', i=i):
                self.assertEqual(
                    binary_search(test_int_array[i], test_array),
                    i
                )

        for i in range(len(test_int_array)):
            with self.subTest('You can found int by ComparableInt', i=i):
                self.assertEqual(
                    binary_search(test_array[i], test_int_array),
                    i
                )

        with self.subTest('Check NotFound raise'):
            self._assertThrowNotFound(0, test_array)
            self._assertThrowNotFound(ComparableInt(0), test_array)

    def test_search_iterable(self):
        """Test that search in list of lists or tuples"""

        test_list_lists_int = sorted([
            [1, 23, 56],
            [4, 63, 123, 3456],
            [0.5, -2]
        ])

        test_list_lists_str = list(map(
            lambda x: list(map(str, x)),
            test_list_lists_int
        ))

        test_list_tuple_int = list(map(tuple, test_list_lists_int))
        test_list_tuple_str = list(map(tuple, test_list_lists_str))

        self._assertEveryElementCanBeFound(test_list_lists_int)
        self._assertEveryElementCanBeFound(test_list_lists_str)
        self._assertEveryElementCanBeFound(test_list_tuple_int)
        self._assertEveryElementCanBeFound(test_list_tuple_str)

        not_in = [[], [374], [1, 23, 56.05]]

        for el in not_in:
            with self.subTest('Test NotFound raise', element=el):
                self._assertThrowNotFound(el, test_list_lists_int)

        for el in not_in:
            with self.subTest('Test NotFound raise', element=el):
                self._assertThrowNotFound(tuple(el), test_list_tuple_int)


if __name__ == '__main__':
    unittest.main()
