from content.models import Platform

INITIAL_SOCIAL_MEDIA_ACCOUNTS = [
    {
        "platform": Platform.INSTAGRAM,
        "username": "panama_in_context",
        "account_id": "12345678",  # This would be the actual Instagram account ID
        "is_active": True,
        "credentials": {
            "access_token": "dummy_access_token",
            "refresh_token": "dummy_refresh_token",
            "token_expiry": "2024-12-31T23:59:59Z",
        },
    }
]
