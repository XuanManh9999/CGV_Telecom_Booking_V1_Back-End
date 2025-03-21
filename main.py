from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import auth
from app.api.v1.endpoints import booking
from app.api.v1.endpoints import phone_number
from app.api.v1.endpoints import provider
from app.api.v1.endpoints import type_number
from app.api.v1.endpoints import report
from app.services.v1.handle_authetication import verify_access_token

app = FastAPI()

#api không cần xác thực
app.include_router(auth.router, prefix="/api/v1", tags=["Auth"])


#api cần xác thực
protected_routers = [
    booking.router,
    phone_number.router,
    type_number.router,
    provider.router,
    report.router
]

for router in protected_routers:
    app.include_router(router, prefix="/api/v1", dependencies=[Depends(verify_access_token)])


# app.add_middleware(CustomMiddleware)

origins = [
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "Welcome To Server Booking"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
    #uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
