import json

def find(predicate, iterator, default=None):
    """
    returns the first element of iterator that matches predicate
    or default if none is found
    """
    try:
        return next((el for el in iterator if predicate(el)))
    except StopIteration:
        return default

class KnownInstances(object):
    def __init__(self, serialised=None, top_slots=3):
        self.instances = list()
        self.top_slots = top_slots
        try:
            unserialised = json.loads(serialised)
            if not isinstance(unserialised, list):
                return self.__default()
            for instance in unserialised:
                if 'instance' in instance and 'hits' in instance:
                    self.instances.append(dict(
                        instance=instance['instance'],
                        hits=instance['hits']
                        ))
        except (json.JSONDecodeError, TypeError):
            self.__default()
            return

    def __default(self):
        self.instances = [{
                "instance": "mastodon.social",
                "hits": 0
            }]

    def clear(self):
        self.instances = []

    def bump(self, instance_name, bump_by=1):
        instance = find(
                lambda i: i['instance'] == instance_name,
                self.instances)
        if not instance:
            instance = dict(instance=instance_name, hits=0)
            self.instances.append(instance)
        instance['hits'] += bump_by

    def normalize(self):
        """
        raises the top `top_slots` instances to the top,
        making sure not to move instances that were already at
        the top
        """
        top_slots = self.top_slots
        head = self.instances[:top_slots]
        tail = self.instances[top_slots:]
        if len(tail) == 0:
            return

        def key(instance):
            return instance['hits']

        for _ in range(top_slots):
            head_min = min(head, key=key)
            tail_max = max(tail, key=key)
            if tail_max['hits'] > head_min['hits']:
                # swap them
                i = head.index(head_min)
                j = tail.index(tail_max)
                buf = head[i]
                head[i] = tail[j]
                tail[j] = buf

            else:
                break

        self.instances = head + tail

    def top(self):
        head = self.instances[:self.top_slots]
        return tuple((i['instance'] for i in head))

    def serialize(self):
        return json.dumps(self.instances)
