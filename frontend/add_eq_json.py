import json

with open("messages/en.json", "r") as f: en = json.load(f)
with open("messages/th.json", "r") as f: th = json.load(f)

en["Home"]["recentEarthquakeTitle"] = "Recent Earthquake"
en["Home"]["noEarthquakeData"] = "No recent earthquake data available."

th["Home"]["recentEarthquakeTitle"] = "แผ่นดินไหวล่าสุด"
th["Home"]["noEarthquakeData"] = "ไม่มีข้อมูลแผ่นดินไหวล่าสุด"

with open("messages/en.json", "w") as f: json.dump(en, f, indent=2)
with open("messages/th.json", "w") as f: json.dump(th, f, indent=2, ensure_ascii=False)
