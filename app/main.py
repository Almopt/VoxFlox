from fastapi import FastAPI
import routes


voxFlowAPI = FastAPI()  # Creates FastAPI instance
voxFlowAPI.include_router(routes.api_v1.router, prefix='/v1')  # Include the routes of the v1



