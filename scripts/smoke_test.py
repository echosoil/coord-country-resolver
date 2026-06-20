from country_resolver import CountryResolver


def main():
    resolver = CountryResolver()

    tests = [
        (41.3874, 2.1686, "Barcelona"),
        (48.8566, 2.3522, "Paris"),
        (35.27595925977908, -2.9557758942246437, "XRXB-4454 / Melilla"),
        ("bad", 2.0, "bad input"),
    ]

    for lat, lon, label in tests:
        r = resolver.resolve(lat, lon)
        print()
        print(label)
        print("country_code:", r.country_code)
        print("source:", r.country_source)
        print("note:", r.country_lookup_note)
        print("matched:", r.matched_country_name)
        print("distance_deg:", r.distance_deg)


if __name__ == "__main__":
    main()