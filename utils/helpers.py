from bot import tusovki, user_sessions

def is_user_in_tusa(user_id: int) -> bool:
    if user_id not in user_sessions:
        return False
    tusa_id = user_sessions[user_id]
    return tusa_id in tusovki and user_id in tusovki[tusa_id]['participants']