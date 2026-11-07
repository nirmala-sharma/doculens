from fastapi.testclient import TestClient
from app import main

client = TestClient(main.app)

def upload(content):
    return client.post(
        "/upload",
        files={"file":("test.pdf",content,"application/pdf")},
    )

def test_upload_is_rate_limited():
   main.limiter.reset()  # start with a clean count

   # The first 5 uploads are allowed (they fail with 400 because the PDF is fake, but they're not blocked)
   for _ in range(5):
       response = upload(b"this is not a real pdf")
       assert response.status_code == 400

    # The 6th upload is blocked with 429
   response = upload(b"this is not a real pdf")
   assert response.status_code == 429
   assert "Rate limit exceeded" in response.json()["error"]

   main.limiter.reset()  # clean up so other tests aren't affected