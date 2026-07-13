# AgroAI Location Demo

Колдонуучунун GPS координаттары боюнча OpenWeather кызматынан аба ырайын алып, өсүмдүккө жөнөкөй климаттык сунуш берген FastAPI демо-долбоору.

## Коопсуздук боюнча маанилүү эскертүү

Репозиторийдин алгачкы commit’инде OpenWeather API ачкычы ачык жарыяланган. Ал ачкычты компрометацияланган деп эсептеп, OpenWeather аккаунтунан **дароо revoke/rotate** кылыңыз. Бул оңдоо ачкычты учурдагы коддон алып салат, бирок эски commit’тин тарыхын автоматтык түрдө өзгөртпөйт.

Жаңы ачкычты GitHub’га же `.env` файлына commit кылбаңыз.

## Мүмкүнчүлүктөр

- координаттарды Pydantic аркылуу текшерүү;
- асинхрондуу OpenWeather суроосу жана 5 секунддук timeout;
- upstream HTTP/JSON каталарын коопсуз иштетүү;
- 5 мүнөттүк in-memory weather cache;
- бир IP үчүн мүнөтүнө 30 суроо чектөөсү;
- бир учурдагы бир нече климаттык коркунучту камтыган сунуш;
- коопсуз DOM жаңыртуусу жана GPS/network каталары үчүн түшүнүктүү билдирүүлөр.

## Талаптар

- Python 3.10 же андан кийинки версия;
- жаңы OpenWeather API ачкычы;
- браузердик геолокация үчүн production’до HTTPS (localhost тестинде HTTPS талап кылынбайт).

## Орнотуу

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:OPENWEATHER_API_KEY="жаңы-ачкыч"
```

macOS же Linux:

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
export OPENWEATHER_API_KEY="жаңы-ачкыч"
```

## Иштетүү

```bash
python -m uvicorn main:app --reload
```

Андан кийин [http://127.0.0.1:8000](http://127.0.0.1:8000) дарегин ачыңыз. API документациясы `/docs` дарегинде жеткиликтүү.

## API

`POST /location`:

```json
{
  "lat": 42.8746,
  "lon": 74.5698
}
```

Координаттардын чектери:

- `lat`: −90…90;
- `lon`: −180…180.

Туура эмес маалымат үчүн FastAPI `422`, OpenWeather катасы үчүн `502`, конфигурация жок болсо `503`, rate limit ашса `429` кайтарат.

## Тесттер

Тесттер чыныгы API ачкычын жана тармакты колдонбойт:

```bash
python -m unittest discover -s tests -v
python -m py_compile main.py weather_service.py recommendation.py
```

GitHub Actions тесттерди Python 3.10, 3.12 жана 3.13 версияларында автоматтык иштетет.

## Production эскертүүлөрү

Cache жана rate limiter азыр бир Python процессинин эсинде гана сакталат. Бир нече worker же сервер колдонулса, Redis сыяктуу жалпы storage керек. Reverse proxy колдонгондо чыныгы client IP туура өткөрүлүп, ишенимдүү proxy конфигурациясы орнотулушу зарыл.
