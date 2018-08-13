import dodo
import doit
from unittest.mock import patch


def test_doit():
    with patch('sys.exit') as exit:
        doit.run(dodo)
        exit.assert_called_with(0)
