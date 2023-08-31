from fastapi import FastAPI
from .routes import api_v1


voxFlowAPI = FastAPI()  # Creates FastAPI instance
voxFlowAPI.include_router(api_v1.router, prefix='/v1')  # Include the routes of the v1



