from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get Supabase JWT secret from environment variables (optional for development)
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Validate the JWT token and extract user information.
    
    Args:
        credentials: The HTTP Authorization credentials containing the JWT token
        
    Returns:
        dict: The decoded JWT payload with user information
        
    Raises:
        HTTPException: If the token is invalid or expired
    """
    try:
        token = credentials.credentials
        
        # Always disable signature verification in development
        # In production, you would set verify_signature to True and provide the JWT secret
        payload = jwt.decode(
            token, 
            SUPABASE_JWT_SECRET if SUPABASE_JWT_SECRET else None, 
            algorithms=["HS256"],
            options={"verify_signature": False}  # In production, this should be True
        )
        
        print(f"Decoded token payload: {payload}")
        
        # Extract user ID from the token - Supabase stores it as sub
        user_id = payload.get("sub")
        if not user_id:
            print("No user_id found in token, checking for custom claim...")
            # Try alternative locations in the payload
            if payload.get("user_id"):
                user_id = payload.get("user_id")
                
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid authentication token: no user ID found")
        
        print(f"Successfully authenticated user: {user_id}")
        return {"user_id": user_id, "email": payload.get("email")}
    except jwt.PyJWTError as e:
        print(f"JWT Error: {str(e)}")
        raise HTTPException(
            status_code=401,
            detail=f"Invalid authentication credentials: {str(e)}"
        )
    except Exception as e:
        print(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Server error during authentication: {str(e)}"
        )
