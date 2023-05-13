from tukaan._collect import collector


TestObject = object()


def test_add_items():
    collector.add("spam", print)  # tukaan_spam_0
    collector.add("ham", print)  # tukaan_ham_0
    collector.add("ham", TestObject)  # tukaan_ham_1

    assert hasattr(collector, "spam")
    assert hasattr(collector, "ham")

    assert collector.spam == {"tukaan_spam_0": print}
    assert collector.ham == {"tukaan_ham_0": print, "tukaan_ham_1": TestObject}


def test_get_by_key():
    assert collector.get_by_key("spam", "nonexistent_key") is None
    assert collector.get_by_key("spam", "tukaan_spam_0") is print
    assert collector.get_by_key("ham", "tukaan_ham_1") is TestObject


def test_get_by_object():
    assert collector.get_by_object("nonexistent_container", "nonexistent_key") is None
    assert collector.get_by_object("spam", "nonexistent_key") is None
    assert collector.get_by_object("spam", print) == "tukaan_spam_0"
    assert collector.get_by_object("ham", TestObject) == "tukaan_ham_1"


def test_remove_by_key():
    assert print in collector.spam.values()
    collector.remove_by_key("spam", "tukaan_spam_0")
    assert print not in collector.spam.values()

    assert TestObject in collector.ham.values()
    collector.remove_by_key("ham", "tukaan_ham_1")
    assert TestObject not in collector.ham.values()

    # Add stuff back
    collector.add("spam", print)  # tukaan_spam_1
    collector.add("ham", TestObject)  # tukaan_ham_2


def test_remove_by_object():
    assert "tukaan_spam_1" in collector.spam
    collector.remove_by_object("spam", print)
    assert "tukaan_spam_1" not in collector.spam

    assert "tukaan_ham_2" in collector.ham
    collector.remove_by_object("ham", TestObject)
    assert "tukaan_ham_2" not in collector.ham
