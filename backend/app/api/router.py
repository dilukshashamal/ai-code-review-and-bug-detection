from fastapi import APIRouter

from app.api.routes.health import router as health_router
from app.graphql.router import graphql_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(graphql_router, prefix="/graphql")
