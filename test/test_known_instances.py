from libforget.known_instances import KnownInstances


def test_known_instances_defaults():
    ki = KnownInstances()
    assert len(ki.instances) == 1
    assert ki.instances[0]['instance'] == 'mastodon.social'
    assert isinstance(ki.instances[0]['hits'], int)


def test_known_instances_clear():
    ki = KnownInstances()
    ki.clear()
    assert len(ki.instances) == 0


def test_known_instances_deserialize():
    ki = KnownInstances(""" [
        {"instance": "chitter.xyz", "hits": 666, "foo": "bar"},
        {"instance": "invalid"}
    ] """)
    assert len(ki.instances) == 1
    assert ki.instances[0]['instance'] == "chitter.xyz"
    assert ki.instances[0]['hits'] == 666


def test_known_instances_bump():
    ki = KnownInstances()
    ki.bump('chitter.xyz')
    assert len(ki.instances) == 2
    assert ki.instances[1]['instance'] == "chitter.xyz"
    assert ki.instances[1]['hits'] == 1

    ki.bump('chitter.xyz')
    assert len(ki.instances) == 2
    assert ki.instances[1]['instance'] == "chitter.xyz"
    assert ki.instances[1]['hits'] == 2


def test_known_instances_normalize_top():
    ki = KnownInstances(None, top_slots=3)
    ki.clear()
    ki.normalize()
    assert len(ki.instances) == 0

    ki.bump("a", 1)
    ki.bump("b", 2)
    ki.bump("c", 3)
    ki.normalize()
    assert ki.instances[0]['instance'] == "a"
    assert ki.instances[1]['instance'] == "b"
    assert ki.instances[2]['instance'] == "c"

    ki.bump("d", 4)
    ki.normalize()
    assert ki.instances[0]['instance'] == "d"
    assert ki.instances[3]['instance'] == "a"

    assert ki.top() == ("d", "b", "c")
