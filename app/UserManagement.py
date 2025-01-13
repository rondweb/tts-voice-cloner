from typing import List

import uvicorn
from fastapi import Depends, FastAPI, HTTPException
from keycloak import KeycloakAdmin
from pydantic import BaseModel

app = FastAPI()

# Keycloak Admin Configuration
keycloak_admin = KeycloakAdmin(
    server_url="https://keycloack-582955622248.northamerica-northeast1.run.app/",
    realm_name="microsaas",
    client_secret_key="fyXlT6zUIxhZ5O4IVD4Rtoz7zmIdSwRq",
    client_id="tts-voice-clone",
    verify=True,
)


# Pydantic models
class User(BaseModel):
    username: str
    email: str
    first_name: str
    last_name: str


class UserInDB(User):
    id: str


# Dependency to get Keycloak admin client
def get_keycloak_admin():
    return keycloak_admin


# Create a new user
@app.post("/users/", response_model=UserInDB)
def create_user(
    user: User, keycloak_admin: KeycloakAdmin = Depends(get_keycloak_admin)
):
    user_id = keycloak_admin.create_user(
        {
            "username": user.username,
            "email": user.email,
            "firstName": user.first_name,
            "lastName": user.last_name,
            "enabled": True,
        }
    )
    return UserInDB(id=user_id, **user.dict())


# Read a user by ID
@app.get("/users/{user_id}", response_model=UserInDB)
def read_user(
    user_id: str, keycloak_admin: KeycloakAdmin = Depends(get_keycloak_admin)
):
    user = keycloak_admin.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserInDB(
        id=user_id,
        username=user["username"],
        email=user["email"],
        first_name=user["firstName"],
        last_name=user["lastName"],
    )


# Update a user
@app.put("/users/{user_id}", response_model=UserInDB)
def update_user(
    user_id: str,
    user: User,
    keycloak_admin: KeycloakAdmin = Depends(get_keycloak_admin),
):
    keycloak_admin.update_user(
        user_id,
        {
            "username": user.username,
            "email": user.email,
            "firstName": user.first_name,
            "lastName": user.last_name,
        },
    )
    return UserInDB(id=user_id, **user.dict())


# Delete a user
@app.delete("/users/{user_id}", response_model=dict)
def delete_user(
    user_id: str, keycloak_admin: KeycloakAdmin = Depends(get_keycloak_admin)
):
    keycloak_admin.delete_user(user_id)
    return {"detail": "User deleted"}


# List all users
@app.get("/users/", response_model=List[UserInDB])
def list_users(keycloak_admin: KeycloakAdmin = Depends(get_keycloak_admin)):
    users = keycloak_admin.get_users()
    return [
        UserInDB(
            id=user["id"],
            username=user["username"],
            email=user["email"],
            first_name=user["firstName"],
            last_name=user["lastName"],
        )
        for user in users
    ]


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
