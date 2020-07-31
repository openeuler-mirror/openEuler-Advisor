"""
reset database
"""
from patch_tracking.app import app
from patch_tracking.database import reset_database


def reset():
    """
    reset database
    """
    with app.app_context():
        reset_database()


if __name__ == "__main__":
    reset()
