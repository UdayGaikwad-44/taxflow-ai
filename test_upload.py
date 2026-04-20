import httpx
import asyncio

async def test_all():
    base_url = "http://localhost:8000/api"
    
    # 1. Register or login to get token
    async with httpx.AsyncClient() as client:
        try:
            reg_resp = await client.post(f"{base_url}/auth/register", json={
                "name": "Test User",
                "email": "testuser@taxflow.ai",
                "password": "testpassword123",
                "user_type": "freelancer"
            })
            token_data = reg_resp.json()
            if reg_resp.status_code == 409: # Already exists
                print("User already exists, logging in...")
                login_resp = await client.post(f"{base_url}/auth/login", json={
                    "email": "testuser@taxflow.ai",
                    "password": "testpassword123"
                })
                token_data = login_resp.json()
        except httpx.ConnectError:
            print("Failed to connect to backend on port 8000. Ensure it's running.")
            return

        token = token_data.get("access_token")
        if not token:
            print(f"Failed to get token: {token_data}")
            return
        
        print("Logged in successfully. Token obtained.")
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Upload Receipt
        with open("test_receipt.jpg", "rb") as f:
            print("Uploading Receipt...")
            receipt_resp = await client.post(
                f"{base_url}/upload/receipt", 
                files={"file": ("test_receipt.jpg", f, "image/jpeg")},
                headers=headers
            )
            print("Receipt Response:", receipt_resp.json())
        
        # 3. Upload Bank Statement
        with open("test_bank.csv", "rb") as f:
            print("Uploading Bank Statement...")
            bank_resp = await client.post(
                f"{base_url}/upload/bank-statement", 
                files={"file": ("test_bank.csv", f, "text/csv")},
                headers=headers
            )
            print("Bank Response:", bank_resp.json())

        # Wait for background jobs a bit
        print("Waiting 10 seconds for backend parsing and OCR jobs to complete...")
        await asyncio.sleep(10)

        # 4. Fetch Receipts
        receipts_resp = await client.get(f"{base_url}/receipts", headers=headers)
        print("Fetched Receipts:", receipts_resp.json())
        
        # 5. Fetch Transactions
        txns_resp = await client.get(f"{base_url}/transactions", headers=headers)
        print("Fetched Transactions Total Items:", len(txns_resp.json()))
        print("Sample Txn:", txns_resp.json()[0] if txns_resp.json() else "None")


if __name__ == "__main__":
    asyncio.run(test_all())
