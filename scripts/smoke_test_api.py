import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "http://127.0.0.1:8010"


def main():
    tests = [
        (41.3874, 2.1686, "Barcelona"),
        (48.8566, 2.3522, "Paris"),
        (35.27595925977908, -2.9557758942246437, "XRXB-4454 / Melilla"),
        ("bad", 2.0, "bad input"),
    ]

    print(requests.get(f"{BASE_URL}/health", timeout=10).json())

    for lat, lon, label in tests:
        response = requests.get(
            f"{BASE_URL}/resolve",
            params={"lat": lat, "lon": lon},
            timeout=10,
        )
        print()
        print(label)
        print(response.status_code)
        print(response.json())


if __name__ == "__main__":
    main()