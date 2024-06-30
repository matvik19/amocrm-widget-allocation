import uvicorn
from fastapi import FastAPI

from src.amo_widget.token_init import initialize_token
from src.amo_widget.routers import router as router_widget
from src.users.routers import router as router_users


app = FastAPI(title="Allocation widget")


app.include_router(router_widget)
app.include_router(router_users)

if __name__ == '__main__':
    initialize_token()

    uvicorn.run("main:app", reload=True)