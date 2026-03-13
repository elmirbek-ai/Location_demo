def recommend(weather):

    temp = weather.get("temperature")
    humidity = weather.get("humidity")

    if temp is None or humidity is None:
        return "Климат маалыматтары жеткиликтүү эмес."

    if humidity > 80:
        return "Нымдуулук өтө жогору. Грибок оорулары чыгуу коркунучу бар."

    if humidity > 70:
        return "Жогорку нымдуулук. Фунгицид колдонуу сунушталат."

    if temp > 30:
        return "Температура жогору. Өсүмдүктү көбүрөөк сугаруу керек."

    if temp < 5:
        return "Температура өтө төмөн. Өсүмдүктү сууктан коргоо керек."

    return "Климат нормалдуу."