from app.routers import (
    auth,
    users,
    subjects,
    flashcards,
    study,
    classes,
    engagement,
    ai,
    system,
)

# Order in which routers are mounted under the /api prefix.
all_routers = [
    auth.router,
    users.router,
    subjects.router,
    flashcards.router,
    study.router,
    classes.router,
    engagement.router,
    ai.router,
    system.router,
]
