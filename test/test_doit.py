import dodo
import doit
from unittest.mock import patch


def test_doit():
    with patch('sys.exit') as _exit:
        with patch('sys.argv'):
            doit.run(dodo)
            _exit.assert_called_with(0)
