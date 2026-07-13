from collections.abc import Mapping


def recommend(weather: Mapping[str, object]) -> str:
    temperature = weather.get("temperature")
    humidity = weather.get("humidity")

    if not isinstance(temperature, (int, float)) or not isinstance(
        humidity,
        (int, float),
    ):
        return "Климат маалыматтары жеткиликтүү эмес."

    recommendations: list[str] = []

    if humidity > 80:
        recommendations.append(
            "Нымдуулук өтө жогору. Грибок оорулары чыгуу коркунучу бар."
        )
    elif humidity > 70:
        recommendations.append(
            "Жогорку нымдуулук. Фунгицид колдонуу сунушталат."
        )

    if temperature > 30:
        recommendations.append(
            "Температура жогору. Өсүмдүктү көбүрөөк сугаруу керек."
        )
    elif temperature < 5:
        recommendations.append(
            "Температура өтө төмөн. Өсүмдүктү сууктан коргоо керек."
        )

    return " ".join(recommendations) or "Климат нормалдуу."
