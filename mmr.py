from db import get_session, User

def update_mmr(username: str, delta: int):
    db = get_session()
    user = db.query(User).filter_by(username=username).first()
    if user:
        user.mmr += delta
        db.commit()
