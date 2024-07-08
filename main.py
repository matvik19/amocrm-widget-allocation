import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from src.amo_widget.token_init import initialize_token
from src.amo_widget.routers import router as router_widget
from src.users.routers import router as router_users


app = FastAPI(title="Allocation widget")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


app.include_router(router_widget)
app.include_router(router_users)


if __name__ == '__main__':
    uvicorn.run("main:app", reload=True)