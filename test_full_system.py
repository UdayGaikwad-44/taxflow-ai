"""
Full End-to-End System Test for TaxFlow AI
Tests: Auth → Bank Upload → Receipt OCR → Transactions → Receipts → AI Chat
"""
import httpx
import asyncio
import json

BASE = "http://localhost:8000/api"
EMAIL = "testuser@taxflow.ai"
PASSWORD = "testpassword123"

PASS = "[PASS]"
FAIL = "[FAIL]"

async def run():
    results = []

    async with httpx.AsyncClient(timeout=60) as c:

        # ─── 1. HEALTH CHECK ──────────────────────────────────────
        r = await c.get("http://localhost:8000/health")
        ok = r.status_code == 200 and r.json().get("status") == "ok"
        results.append((PASS if ok else FAIL, "Health Check", r.json()))

        # ─── 2. AUTH: Login ───────────────────────────────────────
        r = await c.post(f"{BASE}/auth/login", json={"email": EMAIL, "password": PASSWORD})
        if r.status_code == 401:  # user may not exist yet
            r = await c.post(f"{BASE}/auth/register", json={
                "name": "Test User", "email": EMAIL,
                "password": PASSWORD, "user_type": "freelancer"
            })
        ok = r.status_code in (200, 201) and "access_token" in r.json()
        token = r.json().get("access_token", "")
        results.append((PASS if ok else FAIL, "Auth Login/Register", {"status": r.status_code, "token_received": bool(token)}))

        headers = {"Authorization": f"Bearer {token}"}

        # ─── 3. AUTH: /me ─────────────────────────────────────────
        r = await c.get(f"{BASE}/auth/me", headers=headers)
        ok = r.status_code == 200 and "email" in r.json()
        results.append((PASS if ok else FAIL, "GET /auth/me", {"status": r.status_code, "user": r.json().get("email")}))

        # ─── 4. BANK STATEMENT UPLOAD ─────────────────────────────
        csv = ("Transaction Date,Transaction Details,Withdrawals,Deposits\n"
               "2026-04-10,Amazon Shopping,1200.00,\n"
               "2026-04-11,Salary Credit,,80000.00\n"
               "2026-04-12,LIC Premium,5000.00,\n"
               "2026-04-13,JIO Internet,399.00,\n")
        r = await c.post(f"{BASE}/upload/bank-statement",
                         files={"file": ("bank.csv", csv.encode(), "text/csv")},
                         headers=headers)
        ok = r.status_code == 200 and "job_id" in r.json()
        results.append((PASS if ok else FAIL, "POST /upload/bank-statement", {"status": r.status_code, "response": r.json()}))

        # ─── 5. RECEIPT OCR UPLOAD ────────────────────────────────
        try:
            with open("test_receipt.jpg", "rb") as f:
                img_bytes = f.read()
        except FileNotFoundError:
            from PIL import Image, ImageDraw
            img = Image.new("RGB", (300, 200), color="white")
            d = ImageDraw.Draw(img)
            d.text((10, 10), "HDFC Bank Receipt\nAmount: ₹3500\nDate: 2026-04-10\nGSTIN: 27AABCU9603R1ZX", fill=(0, 0, 0))
            import io
            buf = io.BytesIO(); img.save(buf, format="JPEG"); img_bytes = buf.getvalue()

        r = await c.post(f"{BASE}/upload/receipt",
                         files={"file": ("receipt.jpg", img_bytes, "image/jpeg")},
                         headers=headers)
        ok = r.status_code == 200 and "job_id" in r.json()
        results.append((PASS if ok else FAIL, "POST /upload/receipt (OCR)", {"status": r.status_code, "response": r.json()}))

        print("\n>> Waiting 12s for background OCR and parsing jobs...\n")
        await asyncio.sleep(12)

        # ─── 6. TRANSACTIONS LIST ─────────────────────────────────
        r = await c.get(f"{BASE}/transactions", headers=headers)
        ok = r.status_code == 200 and "items" in r.json()
        txns = r.json().get("items", [])
        results.append((PASS if ok else FAIL, "GET /transactions", {
            "status": r.status_code,
            "count": len(txns),
            "categories": list(set(t["category"] for t in txns))
        }))

        # ─── 7. RECEIPTS LIST ─────────────────────────────────────
        r = await c.get(f"{BASE}/receipts", headers=headers)
        ok = r.status_code == 200 and "items" in r.json()
        recs = r.json().get("items", [])
        results.append((PASS if ok else FAIL, "GET /receipts (OCR results)", {
            "status": r.status_code,
            "count": len(recs),
            "merchants": [rec.get("merchant") for rec in recs[:3]]
        }))

        # ─── 8. DEDUCTIONS ────────────────────────────────────────
        r = await c.get(f"{BASE}/deductions", headers=headers)
        results.append((PASS if r.status_code == 200 else FAIL, "GET /deductions", {"status": r.status_code}))

        # ─── 9. TAX REPORT ────────────────────────────────────────
        r = await c.get(f"{BASE}/tax/summary", headers=headers)
        ok = r.status_code == 200
        results.append((PASS if ok else FAIL, "GET /tax/summary", {"status": r.status_code, "data": r.json() if ok else r.text[:200]}))

        # ─── 10. NOTIFICATIONS ────────────────────────────────────
        r = await c.get(f"{BASE}/notifications", headers=headers)
        results.append((PASS if r.status_code == 200 else FAIL, "GET /notifications", {"status": r.status_code}))

        # ─── 11. AI CHAT ──────────────────────────────────────────
        r = await c.post(f"{BASE}/ai/chat",
                         json={"message": "What is my estimated tax liability for FY 2025-26?", "history": []},
                         headers=headers)
        ok = r.status_code == 200 and "reply" in r.json()
        chat_reply = r.json().get("reply", r.text[:200]) if r.status_code == 200 else r.json()
        results.append((PASS if ok else FAIL, "POST /ai/chat (AI Chatbot)", {
            "status": r.status_code,
            "reply_preview": str(chat_reply)[:200]
        }))

    # ─── PRINT RESULTS ────────────────────────────────────────────
    print("\n" + "="*70)
    print("   TAXFLOW AI — FULL END-TO-END TEST RESULTS")
    print("="*70)
    passed = sum(1 for r in results if r[0] == PASS)
    for status, name, detail in results:
        print(f"\n{status}  {name}")
        print(f"   {json.dumps(detail, indent=4, default=str)}")
    print("\n" + "="*70)
    print(f"   TOTAL: {passed}/{len(results)} tests passed")
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(run())
