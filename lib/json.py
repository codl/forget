from json import dumps


def account(acc):
    last_delete = None
    next_delete = None
    if acc.last_delete:
        last_delete = acc.last_delete.isoformat()
    if acc.next_delete:
        next_delete = acc.next_delete.isoformat()
    return dumps(dict(
            post_count=acc.post_count(),
            eligible_for_delete_estimate=acc.estimate_eligible_for_delete(),
            display_name=acc.display_name,
            screen_name=acc.screen_name,
            avatar_url=acc.avatar_url,
            id=acc.id,
            service=acc.service,
            policy_enabled=acc.policy_enabled,
            next_delete=next_delete,
            last_delete=last_delete,
        ))
